#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 4;
use Test::Warnings;

use LandingCompany::Registry;

my @lc_authentication_list = sort { $a cmp $b } ('MX', 'MF', 'MLT');
my @all_lc                 = LandingCompany::Registry->get_all;

subtest 'all landing companies have check' => sub {
    my $is_poi_expiration_check_count = 0;
    my $is_poa_outdated_check_count   = 0;
    foreach my $lc (@all_lc) {
        ok defined($lc->poi_expiration_check_required), 'Got poi_expiration_check_required as a property for ' . $lc->short;
        ++$is_poi_expiration_check_count if $lc->poi_expiration_check_required == 1;

        ok defined($lc->poa_outdated_check_required), 'Got poa_outdated_check_required as a property for ' . $lc->short;
        ++$is_poa_outdated_check_count if $lc->poa_outdated_check_required == 1;
    }

    is $is_poi_expiration_check_count, 6,  'Correct poi_expiration_check_required count for landing companies';
    is $is_poa_outdated_check_count,   9, 'Correct poa_outdated_check_required count for landing companies';
};

subtest 'check default value of poi_expiration_check_required per landing companies' => sub {
    foreach my $lc (@all_lc) {
        my $is_poi_expiration_check_required = $lc->poi_expiration_check_required;
        subtest $lc->short => sub {
            if ($lc->short =~ /^(?:malta|maltainvest|iom|labuan|bvi|vanuatu)$/) {
                is $is_poi_expiration_check_required, 1, 'poi_expiration_check_required is mandatory for ' . $lc->short;
            } else {
                is $is_poi_expiration_check_required, 0, 'poi_expiration_check_required is not mandatory ' . $lc->short;
            }
        };
    }
};

subtest 'check default value of poa_outdated_check_required per landing companies' => sub {
    foreach my $lc (@all_lc) {
        my $is_poa_outdated_check_required = $lc->poa_outdated_check_required;
        subtest $lc->short => sub {
            if ($lc->short =~ /^(?:maltainvest|virtual)$/) {
                is $is_poa_outdated_check_required, 0, 'poa_outdated_check_required is not mandatory for ' . $lc->short;
            } else {
                is $is_poa_outdated_check_required, 1, 'poa_outdated_check_required is mandatory ' . $lc->short;
            }
        };
    }
};

1;
