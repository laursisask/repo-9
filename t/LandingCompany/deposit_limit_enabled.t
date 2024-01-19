#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 2;
use Test::Warnings;

use List::Util qw(any);
use LandingCompany::Registry;

my @deposit_enabled_lc = sort ('malta', 'iom', 'maltainvest');
my @all_lc             = LandingCompany::Registry->get_all;

subtest 'check all landing companies' => sub {
    my $deposit_limit_enabled_count = 0;
    foreach my $lc (@all_lc) {
        ok defined($lc->deposit_limit_enabled), 'Got deposit_limit_enabled as a property for ' . $lc->short;

        if (any { $_ eq $lc->short } @deposit_enabled_lc) {
            is $lc->deposit_limit_enabled, 1, 'deposit limits are enabled for ' . $lc->short;
        } else {
            is $lc->deposit_limit_enabled, 0, 'deposit limits are not enabled for ' . $lc->short;
        }

        ++$deposit_limit_enabled_count if $lc->deposit_limit_enabled == 1;
    }

    is $deposit_limit_enabled_count, scalar @deposit_enabled_lc, 'Correct deposit_limit_enabled count for landing companies';
};

1;
