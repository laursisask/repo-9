#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::Warnings;

use LandingCompany::Registry;

my @all_lc = LandingCompany::Registry->get_all;

subtest 'all landing companies have p2p_available property' => sub {
    my $check_count = 0;
    foreach my $lc (@all_lc) {
        ok defined($lc->p2p_available), 'Got property for ' . $lc->short;
        ++$check_count if $lc->p2p_available == 1;
    }
    is $check_count, 1, 'Correct p2p_available count for landing companies';
};

subtest 'check value per landing company' => sub {
    foreach my $lc (@all_lc) {
        subtest $lc->short => sub {
            if ($lc->short eq 'svg') {
                ok $lc->p2p_available, 'p2p_available is true for ' . $lc->short;
            } else {
                ok !$lc->p2p_available, 'p2p_available is false for ' . $lc->short;
            }
        };
    }
};

done_testing;

1;
