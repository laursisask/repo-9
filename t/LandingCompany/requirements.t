#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::Warnings;

use LandingCompany::Registry;

# This is a safety check for accidental changes to LC field requirements.
# This test must be updated whenever a LC's requirements are changed.

my $baseline = {
    iom => {
        signup => [
            qw (salutation
                citizen
                first_name
                last_name
                date_of_birth
                residence
                address_line_1
                address_city
                address_postcode )
        ],
    },
    malta => {
        signup => [
            qw ( salutation
                citizen
                first_name
                last_name
                date_of_birth
                residence
                address_line_1
                address_city )
        ],
    },
    maltainvest => {
        signup => [qw (
                salutation
                citizen
                tax_residence
                tax_identification_number
                first_name
                last_name
                date_of_birth
                residence
                address_line_1
                address_city
                account_opening_reason
            )
        ],
    },
    svg => {
        signup => [qw (
                first_name
                last_name
                residence
                date_of_birth
            )
        ],
        withdrawal => [qw (
                address_line_1
                address_city
            )
        ],
    },
    virtual => {},
    vanuatu => {
        signup => [qw(
                citizen
                place_of_birth
                tax_residence
                tax_identification_number
                account_opening_reason
            )
        ],
        compliance => {
            mt5             => [qw/fully_authenticated expiration_check/],
            tax_information => [qw/tax_residence tax_identification_number/],
        },
        after_first_deposit => {financial_assessment => [qw/financial_information/]}
    },
    labuan => {
        signup => [qw (
                phone
                citizen
                account_opening_reason
            )
        ],
        compliance => {
            mt5             => [qw/fully_authenticated expiration_check/],
            tax_information => [qw/tax_residence tax_identification_number/],
        },
    },
    bvi => {
        compliance => {
            mt5             => [qw/fully_authenticated expiration_check/],
            tax_information => [qw/tax_residence tax_identification_number/],
        },
    },
};

subtest 'compare requirements against baseline' => sub {
    foreach my $lc (keys %$baseline) {
        my $requirements = LandingCompany::Registry->by_name($lc)->requirements;

        if ($baseline->{$lc}->%*) {
            for my $req (keys $baseline->{$lc}->%*) {
                cmp_bag $requirements->{$req}, $baseline->{$lc}{$req}, "$req requirements for $lc" if ref $requirements->{$req} eq 'ARRAY';
                cmp_deeply $requirements->{$req}, $baseline->{$lc}{$req}, "$req requirements for $lc" if ref $requirements->{$req} eq 'HASH';
            }
        } else {
            cmp_deeply $requirements, {}, "no requirements for $lc";
        }
    }

};

done_testing;
