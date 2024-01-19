#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::Warnings;

use LandingCompany::Registry;

# This is a safety check for accidental changes to LC field actions.
# This test must be updated whenever a LC's actions are changed.

my $baseline = {
    iom         => {},
    malta       => {first_deposit => [qw(age_verified)]},
    maltainvest => {first_deposit => [qw(fully_auth_check)]},
    svg         => {
        #TODO: change this action to arrayref like other landing complanies
        account_verified => {email_client => 1},
    },
    virtual => {},
    vanuatu => {},
    labuan  => {signup => [qw(sanctions)]},
};

subtest 'compare requirements against baseline' => sub {

    foreach my $lc (keys %$baseline) {
        my $actions = LandingCompany::Registry->by_name($lc)->actions;

        is_deeply $actions, $baseline->{$lc}, "actions for $lc";
    }

};

done_testing;
