#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 3;
use Test::Warnings;

use LandingCompany::Registry;

my @all_lc = LandingCompany::Registry->get_all;

subtest 'all landing companies have check' => sub {
    my $required_consent_count = 0;
    foreach my $lc (@all_lc) {
        ok $lc->marketing_email_consent, 'Got email consent for ' . $lc->short;
        ++$required_consent_count if $lc->marketing_email_consent->{required};
    }

    is $required_consent_count, 3, 'Correct consent count for landing companies';
};

subtest 'check default value of email consent per landing companies' => sub {
    foreach my $lc (@all_lc) {
        my $marketing_email_consent = $lc->marketing_email_consent;
        subtest $lc->short => sub {
            if ($lc->short =~ /^(?:malta|iom)$/) {
                is $marketing_email_consent->{required}, 1, 'Email consent is mandatory';
                is $marketing_email_consent->{default},  0, 'Email consent defaults to 0';
            } elsif ($lc->short =~ /^(?:maltainvest)$/) {
                is $marketing_email_consent->{required}, 1, 'Email consent is mandatory';
                is $marketing_email_consent->{default},  1, 'Email consent defaults to 1';
            } else {
                is $marketing_email_consent->{required}, 0, 'Email consent is not mandatory';
                is $marketing_email_consent->{default},  1, 'Email consent defaults to 1';
            }
        };
    }
};
