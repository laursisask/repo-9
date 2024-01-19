package LandingCompany::Commission;

use strict;
use warnings;

=head1 NAME

LandingCompany::Commission

=head1 DESCRIPTION

This class represents landing company's specific base commission for an underlying.

=cut

## VERSION

use Syntax::Keyword::Try;
use Log::Any qw($log);

use Finance::Underlying;
use Exporter qw(import);
use LandingCompany::Utility;

our @EXPORT_OK = qw(get_underlying_base_commission);

my $commissions = LandingCompany::Utility::load_yml('commission.yml');

=head2 get_underlying_basecommission

->get_underlying_base_commission('svg', 'frxUSDJPY');

Returns the base commission for a given landing company and underlying symbol.

=cut

sub get_underlying_base_commission {
    my $args = shift;

    die 'underlying symbol is required' unless $args->{underlying_symbol};

    my $lc       = $args->{landing_company} // 'svg';
    my $u_symbol = $args->{underlying_symbol};
    my $u_config = undef;

    try {
        $u_config = Finance::Underlying->by_symbol($u_symbol);
    } catch ($e) {
        $log->debug($e);
    }

    my $lc_comm = $commissions->{$lc};

    die 'could not find base commission for ' . $lc unless $lc_comm;

    return $lc_comm->{$u_symbol}            if $lc_comm->{$u_symbol};
    return $lc_comm->{$u_config->submarket} if $u_config->submarket and $lc_comm->{$u_config->submarket};
    return $lc_comm->{$u_config->market}    if $u_config->market    and $lc_comm->{$u_config->market};

    warn 'base commission for ' . $u_symbol . ' not set. Setting it to 0.05.';
    return 0.05;

}

1;
