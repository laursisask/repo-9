package LandingCompany::Registry;
use strict;
use warnings;
use List::Util qw(any);

use LandingCompany;
use LandingCompany::Utility;

use LandingCompany::BVI;
use LandingCompany::DSL;
use LandingCompany::IOM;
use LandingCompany::Labuan;
use LandingCompany::Malta;
use LandingCompany::MaltaInvest;
use LandingCompany::Samoa;
use LandingCompany::SamoaVirtual;
use LandingCompany::SVG;
use LandingCompany::Vanuatu;
use LandingCompany::Virtual;

## VERSION

my (%all_currencies, @all_broker_codes, @all_real_broker_codes);
my $loaded_landing_companies;
my ($broker_to_name, $sub_landing_companies, @all_valid_landing_companies);

=head1 DESCRIPTION

Factory to build instance for all landing companies.

=cut

=head2 load_config

Loads landing companies config from file.

=cut

sub load_config {
    # Reset landing company indexes
    ($broker_to_name, $sub_landing_companies, %all_currencies, @all_valid_landing_companies, @all_broker_codes, @all_real_broker_codes) = ();

    my %name_to_class = (
        'bvi'           => 'BVI',
        'dsl'           => 'DSL',
        'iom'           => 'IOM',
        'labuan'        => 'Labuan',
        'malta'         => 'Malta',
        'maltainvest'   => 'MaltaInvest',
        'samoa'         => 'Samoa',
        'samoa-virtual' => 'SamoaVirtual',
        'svg'           => 'SVG',
        'vanuatu'       => 'Vanuatu',
        'virtual'       => 'Virtual',
    );

    $loaded_landing_companies = LandingCompany::Utility::load_yml('landing_companies.yml');
    for my $k (sort keys %$loaded_landing_companies) {
        my $v = $loaded_landing_companies->{$k};
        if ($v->{is_disabled}) {
            delete $loaded_landing_companies->{$k};
            next;
        }

        $v->{name} ||= $k;
        my $sub_class = $name_to_class{$v->{short}};
        my $lc        = "LandingCompany::$sub_class"->new($v);
        $sub_landing_companies->{$v->{short}} = $lc;
        $sub_landing_companies->{$k} = $lc;

        for my $alias ($v->{aliases}->@*) {
            $sub_landing_companies->{$alias} = $lc;
        }

        push @all_valid_landing_companies, $lc;
        push @all_broker_codes,            @{$v->{broker_codes}};
        push @all_real_broker_codes,       @{$v->{broker_codes}} unless $lc->is_virtual;
        @all_currencies{keys %{$v->{legal_allowed_currencies}}} = values %{$v->{legal_allowed_currencies}};
        $broker_to_name->{$_} = $v->{short} for @{$v->{broker_codes}};

    }

    return undef;
}

BEGIN {
    load_config();
}

=head2 get_loaded_landing_companies

Returns a list of all landing companies (raw from yml file)

=cut

sub get_loaded_landing_companies {
    return $loaded_landing_companies;
}

=head2 all_currencies

Returns a list of all available currencies for which we have landing companies.

=cut

sub all_currencies {
    my ($self) = @_;
    return keys %all_currencies;
}

=head2 all_crypto_currencies

Returns a list of all available crypto currencies for which we have landing companies.

=cut

sub all_crypto_currencies {
    my ($self) = @_;
    return grep { $all_currencies{$_}->{type} eq 'crypto' } keys %all_currencies;
}

=head2 all_broker_codes

Returns a list of all defined broker codes

=cut

sub all_broker_codes {
    return @all_broker_codes;
}

=head2 all_real_broker_codes

Returns a list of all defined real broker codes

=cut

sub all_real_broker_codes {
    return @all_real_broker_codes;
}

=head2 get_currency_definition

Returns the following arrayref containing the currency definition data or undef if not legal currency:

    {
        type         => Str  # 'fiat' or 'crypto'
        stable       => Str  # If stable, contains code of currency this is pegged to (e.g. 'USD')
    }

=cut

sub get_currency_definition {
    my $currency            = shift;
    my $currency_definition = $all_currencies{$currency // ''};
    return undef if not defined $currency_definition;
    return $currency_definition;
}

=head2 get_currency_type

Returns type of currency or undef if not legal currency

=cut

sub get_currency_type {
    my $currency            = shift;
    my $currency_definition = get_currency_definition($currency);
    return '' if ref $currency_definition ne 'HASH';
    return $currency_definition->{type};
}

=head2 get_ip_check_broker_codes

Returns landing_companies that needed ip_check

=cut

sub get_ip_check_broker_codes {
    my @lc_list;
    map { $loaded_landing_companies->{$_}->{ip_check_required} && push @lc_list, $loaded_landing_companies->{$_}{broker_codes}->@* }
        keys %$loaded_landing_companies;
    return @lc_list;
}

=head2 get_crypto_enabled_broker_codes

Returns a list of cryptocurrency-enabled landing company broker codes (eg. C<CR> or C<MX>)

=cut

sub get_crypto_enabled_broker_codes {
    return map {
        # Flatten out list of broker codes
        $_->{broker_codes}->@*
    } grep {
        # Only include this landing company if it has any cryptocurrencies
        any { $_->{type} eq 'crypto' } values $_->{legal_allowed_currencies}->%*
    } @all_valid_landing_companies;
}

=head2 check_valid_broker_short_code

    LandingCompany::Registry->check_valid_broker_short_code($broker_code);

Check the given broker code is valid / active broker code.

Takes the following parameter

=over 4

=item * C<broker_code>

=back

Returns 1 if the broker code exists in broker code list, otherwise 0.

=cut

sub check_valid_broker_short_code {
    my ($class, $broker_code) = @_;
    return any { $broker_code eq $_ } @all_broker_codes;
}

=head2 check_broker_from_loginid

Returns 1 if loginid contains valid broker code, otherwisde 0.

=cut

sub check_broker_from_loginid {
    my ($class, $loginid) = @_;
    my $broker_code = $class->broker_code_from_loginid($loginid);
    return $broker_code && $class->check_valid_broker_short_code($broker_code);
}

=head2 broker_code_from_loginid

Returns the broker code to the given loginid

=cut

sub broker_code_from_loginid {
    my ($self, $loginid) = @_;

    my ($broker_code) = $loginid =~ /^([A-Z]+)[0-9]+$/;

    return $broker_code;
}

=head2 by_name

Returns the landing company associated with the given name

=cut

sub by_name {
    my ($class, $name) = @_;

    return $sub_landing_companies->{$name};
}

=head2 by_broker

Returns the landing company corresponding to the given broker code

=cut

sub by_broker {
    my ($class, $broker) = @_;
    my $name = $broker_to_name->{$broker};
    return $name ? $class->by_name($name) : undef;
}

=head2 by_loginid

Returns the landing company corresponding to the given loginid

=cut

sub by_loginid {
    my ($class, $loginid) = @_;
    my $broker_code = $class->broker_code_from_loginid($loginid);
    die "unable to extract broker code from $loginid" unless $broker_code;
    return $class->by_broker($broker_code);
}

=head2 get_all

Returns a list of all landing company objects

=cut

sub get_all {
    return @all_valid_landing_companies;
}

=head2 get_default_company

Returns the default landing company. Currently C<virtual>.

=cut

sub get_default_company {
    my ($class) = @_;
    return $class->by_name('virtual');
}

1;
