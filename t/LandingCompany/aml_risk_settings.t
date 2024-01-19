#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More;
use Test::Warnings;
use Test::Deep;

use LandingCompany::Registry;

my $risk_settings = {
    svg         => bag(qw/aml_thresholds/),
    maltainvest => bag(qw/aml_thresholds aml_jurisdiction/),
    labuan      => bag(qw/mt5_thresholds mt5_jurisdiction/),
    vanuatu     => bag(qw/mt5_thresholds mt5_jurisdiction/),
    bvi         => bag(qw/mt5_thresholds mt5_jurisdiction/),
};

my $risk_lookup = {
    svg         => {aml_thresholds => 1},
    maltainvest => {
        aml_thresholds   => 1,
        aml_jurisdiction => 1
    },
    labuan => {
        mt5_thresholds   => 1,
        mt5_jurisdiction => 1
    },
    vanuatu => {
        mt5_thresholds   => 1,
        mt5_jurisdiction => 1
    },
    bvi => {
        mt5_thresholds   => 1,
        mt5_jurisdiction => 1
    },
};

my @all_lc = LandingCompany::Registry->get_all;

subtest 'check all landing companies' => sub {
    my $jurisdiction_enabled_count = 0;
    my $thresholds_enabled_count   = 0;
    foreach my $lc (@all_lc) {
        ok defined($lc->risk_settings), 'Got risk_ratings as a property for ' . $lc->short;

        cmp_deeply $lc->risk_settings, $risk_settings->{$lc->short} // [], 'Risk settings content is correct for ' . $lc->short;

        is_deeply $lc->risk_lookup, $risk_lookup->{$lc->short} // {}, 'Risk lookup table is correct for ' . $lc->short;
    }
};

done_testing();

1;
