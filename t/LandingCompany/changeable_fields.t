#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::Warnings;

use LandingCompany::Registry;

my @all_lc = LandingCompany::Registry->get_all;

my %expected = (
    svg => {
        only_before_auth => [
            qw(salutation first_name last_name date_of_birth citizen account_opening_reason
                tax_residence tax_identification_number)
        ],
        personal_details_not_locked => [qw(first_name last_name date_of_birth citizen place_of_birth)],
    },
    vanuatu => {
        only_before_auth => [qw(tax_residence tax_identification_number)],
    },
    maltainvest => {
        only_before_auth => [
            qw(salutation first_name last_name date_of_birth citizen account_opening_reason
                tax_residence tax_identification_number)
        ],
        personal_details_not_locked => [qw(first_name last_name date_of_birth citizen place_of_birth)],
    },
    malta => {
        only_before_auth => [
            qw(salutation first_name last_name date_of_birth citizen account_opening_reason
                tax_residence tax_identification_number)
        ],
        personal_details_not_locked => [qw(first_name last_name date_of_birth citizen place_of_birth)],
    },
    dsl => {
        only_before_auth => [
            qw(salutation first_name last_name date_of_birth citizen account_opening_reason
                tax_residence tax_identification_number)
        ],
        personal_details_not_locked => [qw(first_name last_name date_of_birth citizen place_of_birth)],
    },
);

subtest 'check if changeable fields are corrrect' => sub {
    foreach my $lc (@all_lc) {
        my $changeable = $lc->changeable_fields;

        is_deeply $changeable, $expected{$lc->short} // {}, "changeble_fields are correct for " . $lc->short;
    }

};

done_testing();
