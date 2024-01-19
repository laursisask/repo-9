#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::Warnings;

use LandingCompany::Registry;

my @all_lc = LandingCompany::Registry->get_all;

subtest 'Residences default currency' => sub {
    foreach my $lc (@all_lc) {
        subtest $lc->short => sub {
            ok $lc->residences_default_currency, $lc->short . ' has residences default currency';

            if ($lc->short eq 'maltainvest') {
                is $lc->residences_default_currency->{gb}, 'GBP', 'GBP is the currency for gb residence';
            } elsif ($lc->short eq 'iom') {
                is $lc->residences_default_currency->{gb}, 'GBP', 'GBP is the currency for gb residence';
            } elsif ($lc->short eq 'svg') {
                is $lc->residences_default_currency->{au}, 'AUD', 'AUD is the currency for au residence';
            }
        };
    }
};

done_testing;

1;
