#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 3;
use Test::Warnings;

use LandingCompany::Registry;

my @lc_authentication_list = sort { $a cmp $b } ('MX', 'MF', 'MLT');
my @all_lc                 = LandingCompany::Registry->get_all;

subtest 'all landing companies have check' => sub {
    my $is_authentication_mandatory_count = 0;
    foreach my $lc (@all_lc) {
        ok defined($lc->is_authentication_mandatory), 'Got is_authentication_mandatory as a property for ' . $lc->short;
        ++$is_authentication_mandatory_count if $lc->is_authentication_mandatory == 1;
    }

    is $is_authentication_mandatory_count, 6, 'Correct is_authentication_mandatory count for landing companies';
};

subtest 'check default value of is_authentication_mandatory per landing companies' => sub {
    foreach my $lc (@all_lc) {
        my $is_authentication_mandatory = $lc->is_authentication_mandatory;
        subtest $lc->short => sub {
            if ($lc->short =~ /^(?:malta|maltainvest|iom|labuan|bvi|svg)$/) {
                is $is_authentication_mandatory, 1, 'is_authentication_mandatory is mandatory for ' . $lc->short;
            } else {
                is $is_authentication_mandatory, 0, 'is_authentication_mandatory is not mandatory ' . $lc->short;
            }
        };
    }
};

1;
