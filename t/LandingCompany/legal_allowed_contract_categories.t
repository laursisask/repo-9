#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 2;
use Test::Deep;
use Test::Warnings;

use LandingCompany::Registry;

my $all_eu = [qw(
        callputequal
        asian
        callput
        digits
        endsinout
        staysinout
        touchnotouch
        reset
        lookback
        highlowticks
        callputspread
    )];
my $non_eu      = ['runs'];
my $vrtc_only   = ['multiplier'];
my $accumulator = ['accumulator'];
my $turbos      = ['turbos'];
my $vanilla     = ['vanilla'];

subtest 'legal allowed contract categories' => sub {
    my $cc = LandingCompany::Registry->by_loginid('MF123123')->legal_allowed_contract_categories;
    cmp_bag($cc, [@$vrtc_only], 'MF has vrtc_only contract categories');
    $cc = LandingCompany::Registry->by_loginid('MLT123123')->legal_allowed_contract_categories;
    cmp_bag($cc, [@$non_eu, @$all_eu], 'MLT has all_eu and non_eu contract categories');
    $cc = LandingCompany::Registry->by_loginid('MX123123')->legal_allowed_contract_categories;
    cmp_bag($cc, [@$non_eu, @$all_eu], 'MX has all_eu and non_eu contract categories');
    $cc = LandingCompany::Registry->by_loginid('CR123123')->legal_allowed_contract_categories;
    cmp_bag($cc, [@$non_eu, @$all_eu, @$vrtc_only, @$accumulator, @$vanilla, @$turbos], 'CR has all contract categories');
    $cc = LandingCompany::Registry->by_loginid('VRTC123123')->legal_allowed_contract_categories;
    cmp_bag($cc, [@$non_eu, @$all_eu, @$vrtc_only, @$accumulator, @$turbos, @$vanilla], 'VRTC has all contract categories');
};
