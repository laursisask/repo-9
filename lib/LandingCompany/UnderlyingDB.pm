package LandingCompany::UnderlyingDB;

use strict;
use warnings;

use MooseX::Singleton;

## VERSION

=head1 NAME

LandingCompany::UnderlyingDB

=head1 SYNOPSIS

    my $udb     = LandingCompany::UnderlyingDB->instance;
    my @symbols = $udb->get_symbols_for(
        market            => 'forex',
        contract_category => 'endsinout',
        expiry_type       => 'intraday'
    );
    my $sym_props = $udb->get_parameters_for('frxEURUSD');

=head1 DESCRIPTION

This module implements functions to access information from underlyings.yml.
The class is a singleton. You do not need to explicitly initialize class,
it will be initialized automatically then you will try to get instance. By
default it reads information from underlyings.yml. It periodically checks
if underlyings.yml was changed and if it is reloads data.

=cut

use namespace::autoclean;
use List::Util      qw(first);
use List::MoreUtils qw( uniq );
use Memoize;

use Finance::Contract::Category;
use Finance::Underlying;
use Finance::Underlying::Market::Registry;
use Finance::Underlying::SubMarket::Registry;
use Finance::Underlying::Market;
use Finance::Underlying::SubMarket;

has quant_config => (
    is => 'rw',
);

has offerings_flyby => (
    is => 'rw',
);

has offerings_flyby_all => (
    is => 'rw',
);

has chronicle_reader => (
    is => 'rw',
);

=head2 symbols_for_intraday_fx

The standard list of non RMG underlyings which have active bets anywhere.

Convenience wrapper for L</get_symbols_for>.

=cut

sub symbols_for_intraday_fx {
    my ($self, $exclude_suspended) = @_;

    my $flag = (defined $exclude_suspended and $exclude_suspended) ? 1 : 0;

    my @symbols = (
        $self->get_symbols_for(
            market            => [qw(forex commodities)],
            contract_category => 'callput',
            expiry_type       => 'intraday',
            start_type        => 'spot',
            exclude_suspended => $flag,
        ),
        $self->get_symbols_for(
            market            => 'synthetic_index',
            submarket         => [qw(forex_basket commodity_basket)],
            contract_category => 'callput',
            expiry_type       => 'intraday',
            start_type        => 'spot',
            exclude_suspended => $flag,
        ));

    return @symbols;
}

=head2 symbols_for_intraday_index

The list of index that has intraday contracts.

=cut

sub symbols_for_intraday_index {
    my $self    = shift;
    my @symbols = (
        $self->get_symbols_for(
            market            => 'indices',
            contract_category => 'callput',
            expiry_type       => 'intraday',
            start_type        => 'spot',
        ));

    return @symbols;
}

=head2 markets

Return list of all markets

=cut

sub markets {
    my $self = shift;
    my @markets =
        map { $_->name } Finance::Underlying::Market::Registry->instance->display_markets;
    return @markets;
}

=head2 get_symbols_for

Return list of symbols satisfying given conditions. You can specify following I<%filter_args>:

=over 4

=item market

Return only symbols for given market. This argument is required. This argument
may be array refference if you want to get symbols for several markets.

=item submarket

Return only symbols for the given submarket.  This is optional.  Specifying a
miatched market and submarket will result in an empty response

=item contract_category

Return only symbols for which given contract_category is available. contract_category may be one
of the returned by the available_contract_categories function, or "IV" which means
at least one of the callput, endsinout, touchnotouch, staysinout, or "ANY"
which means that some contract_categories should be enabled for symbol. If contract_category
is not specified, function will return all symbols for given market including
the inactive ones (for which not any bet types available).

=item expiry_type

Return only those symbols which match both the bet type and the supplied expiry_type

=item exclude_disabled

Changes filter behavior to disallow listing of symbols which have buying/trading suspended.

=back

Example usage:

    $self->get_symbols_for(%filter_args)

=cut

sub get_symbols_for {
    my ($self, %args) = @_;
    die("market is not specified!")
        unless $args{market};

    $args{contract_category} = $args{contract_category}->code
        if (ref $args{contract_category});

    my @underlyings;
    my %disabled;
    if ($args{exclude_suspended}) {
        my $ul_info = $self->quant_config;
        %disabled = map { $_ => 1 } uniq(@{$ul_info->suspend_buy}, @{$ul_info->suspend_trades});
    }
    my $markets = ref $args{market} ? $args{market} : [$args{market}];
    for (@$markets) {
        $args{market} = $_;
        foreach my $symbol ($self->_get_symbols_for(%args)) {
            push @underlyings, $symbol unless ($disabled{$symbol});
        }
    }

    return @underlyings;
}

sub _get_symbols_for {
    my ($self, %args) = @_;
    foreach my $any_is_default (qw(expiry_type submarket)) {
        delete $args{$any_is_default}
            if ($args{$any_is_default} and $args{$any_is_default} eq 'ANY');
    }

    die 'Cannot specify expiry_type without specifying contract_category'
        if ($args{expiry_type} and not $args{contract_category});

    if ($args{expiry_type}
        and not first { $args{expiry_type} eq $_ } $self->available_expiry_types)
    {
        die 'Supplied expiry_type[' . $args{expiry_type} . '] is not listed in available_expiry_types';
    }

    if ($args{start_type}
        and not first { $args{start_type} eq $_ } $self->available_start_types)
    {

        die 'Supplied start_type[' . $args{start_type} . '] is not listed in available_start_types';
    }

    my @current_list =
        grep { $_->market eq $args{market} } map { Finance::Underlying->by_symbol($_->symbol) } Finance::Underlying->all_underlyings;

    if (defined $args{submarket}) {
        my @submarket = ref $args{submarket} ? @{$args{submarket}} : ($args{submarket});
        my @new_list;
        foreach my $sub (@submarket) {
            push @new_list, grep { $_->submarket eq $sub } @current_list;
        }
        @current_list = @new_list;
    }

    if ($args{quanto_only}) {
        @current_list = grep { $_->quanto_only } @current_list;
    } elsif ($args{contract_category}) {
        @current_list = grep { !$_->quanto_only } @current_list;

        my $contract_categories =
              ($args{contract_category} eq 'ANY') ? [$self->available_contract_categories]
            : ($args{contract_category} eq 'IV')  ? [$self->available_iv_categories]
            :                                       [$args{contract_category}];

        my $expiry_types =
              ($args{expiry_type})
            ? [$args{expiry_type}]
            : [$self->available_expiry_types];
        my $start_types =
              ($args{start_type})
            ? [$args{start_type}]
            : [$self->available_start_types];
        my $barrier_categories =
              ($args{barrier_category})
            ? [$args{barrier_category}]
            : [Finance::Contract::Category->get_all_barrier_categories];

        @current_list =
            grep { (_matches_types($self, $_, $expiry_types, $start_types, $contract_categories, $barrier_categories, $args{exclude_suspended})) }
            @current_list;
    }

    return map { $_->symbol } @current_list;
}

memoize('_get_symbols_for', NORMALIZER => '_normalize_method_args');

sub _matches_types {
    my ($self, $asset, $expiry_types, $start_types, $contract_categories, $barrier_categories, $exclude_suspended) = @_;

    my $args = {
        underlying_symbol => $asset->{symbol},
        barrier_category  => $barrier_categories,
        contract_category => $contract_categories,
        start_type        => $start_types,
        expiry_type       => $expiry_types,
    };

    my $offerings = $exclude_suspended ? $self->offerings_flyby : $self->offerings_flyby_all;

    return $offerings->query($args);
}

sub _normalize_method_args {
    my ($self, %args) = @_;
    return join "\0", map { $_ => $args{$_} } sort keys %args;
}

=head2 $self->available_contract_categories

Return list of all available contract categories

=cut

sub available_contract_categories {
    return
        qw(asian digits callput endsinout touchnotouch staysinout lookback highlowticks reset callputspread callputequal runs multiplier accumulator turbos vanilla);
}

=head2 $self->available_expiry_types

Return list of all available bet sub types

=cut

sub available_expiry_types {
    return qw(intraday daily tick no_expiry);
}

=head2 $self->available_start_types

Return list of all available start types

=cut

sub available_start_types {
    return qw(spot forward);
}

=head2 $self->available_iv_categories

Return list of all available iv contract categories

=cut

sub available_iv_categories {
    return qw(callput endsinout touchnotouch staysinout);
}

__PACKAGE__->meta->make_immutable(inline_constructor => 0);

1;
