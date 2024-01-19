#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::Deep;
use Test::FailWarnings;
use Test::MockTime qw(set_absolute_time);

use LandingCompany::Registry;

my $offerings_config = {
    action          => 'buy',
    loaded_revision => 2,
};

subtest 'uk residence' => sub {
    subtest 'binary_smarttrader' => sub {
        my $o               = LandingCompany::Registry->by_name('iom')->basic_offerings_for_country('gb', $offerings_config, 'binary_smarttrader');
        my @expected_market = qw();
        my @expected_contract_category = qw();
        my @expected_underlying_symbol = qw();
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = 0;
        is $o->query({}), $expected_count, 'offerings count';
    };

    subtest 'deriv_dtrader' => sub {
        my $o               = LandingCompany::Registry->by_name('iom')->basic_offerings_for_country('gb', $offerings_config, 'deriv_dtrader');
        my @expected_market = qw();
        my @expected_contract_category = qw();
        my @expected_underlying_symbol = qw();
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = 0;
        is $o->query({}), $expected_count, 'offerings count';
    };
};

subtest 'iom residence + binary_smarttrader' => sub {
    my $o               = LandingCompany::Registry->by_name('iom')->basic_offerings_for_country('im', $offerings_config, 'binary_smarttrader');
    my @expected_market = qw();
    my @expected_contract_category = qw();
    my @expected_underlying_symbol = qw();
    is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
    is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
    is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
    my $expected_count = {
        normal       => 0,
        quiet_period => 0
    };
    is $o->query({}), $expected_count->{($o->is_quiet_period ? 'quiet_period' : 'normal')}, 'offerings count';
};

subtest 'australia residence' => sub {
    subtest 'binary_smarttrader' => sub {
        my $o               = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('au', $offerings_config, 'binary_smarttrader');
        my @expected_market = qw();
        my @expected_contract_category = qw();
        my @expected_underlying_symbol = qw();
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = 0;
        is $o->query({}), $expected_count, 'offerings count';
    };
    subtest 'deriv_dtrader' => sub {
        my $o               = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('au', $offerings_config, 'deriv_dtrader');
        my @expected_market = qw(forex synthetic_index);
        my @expected_contract_category = qw(multiplier);
        my @expected_underlying_symbol = qw(
            frxAUDJPY
            frxAUDUSD
            frxEURAUD
            frxEURCAD
            frxEURCHF
            frxEURGBP
            frxEURJPY
            frxEURUSD
            frxGBPAUD
            frxGBPJPY
            frxGBPUSD
            frxUSDCAD
            frxUSDCHF
            frxUSDJPY
            WLDAUD
            WLDEUR
            WLDGBP
            WLDUSD
            WLDXAU
        );
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = 38;
        is $o->query({}), $expected_count, 'offerings count';
    };
    subtest 'binary_bot' => sub {
        my $o                          = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('au', $offerings_config, 'binary_bot');
        my @expected_market            = qw();
        my @expected_contract_category = qw();
        my @expected_underlying_symbol = qw();
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = 0;
        is $o->query({}), $expected_count, 'offerings count';
    };
};

subtest 'singapore residence' => sub {
    subtest 'binary_smarttrader' => sub {
        my $o               = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('sg', $offerings_config, 'binary_smarttrader');
        my @expected_market = qw(forex commodities indices);
        my @expected_contract_category = qw(callput callputequal touchnotouch endsinout staysinout);
        my @expected_underlying_symbol = qw(
            OTC_AEX
            OTC_AS51
            OTC_DJI
            OTC_FCHI
            OTC_FTSE
            OTC_GDAXI
            OTC_HSI
            OTC_IBEX35
            OTC_N225
            OTC_NDX
            OTC_SPC
            OTC_SSMI
            OTC_SX5E
            frxAUDCAD
            frxAUDCHF
            frxAUDJPY
            frxAUDNZD
            frxAUDUSD
            frxBROUSD
            frxEURAUD
            frxEURCAD
            frxEURCHF
            frxEURGBP
            frxEURJPY
            frxEURNZD
            frxEURUSD
            frxGBPAUD
            frxGBPCAD
            frxGBPCHF
            frxGBPJPY
            frxGBPNOK
            frxGBPNZD
            frxGBPPLN
            frxGBPUSD
            frxNZDJPY
            frxNZDUSD
            frxUSDCAD
            frxUSDCHF
            frxUSDJPY
            frxUSDMXN
            frxUSDNOK
            frxUSDPLN
            frxUSDSEK
            frxXAGUSD
            frxXAUUSD
            frxXPDUSD
            frxXPTUSD
        );
        is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
        is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
        is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
        my $expected_count = {
            normal       => 632,
            quiet_period => 632,
        };
        is $o->query({}), $expected_count->{($o->is_quiet_period ? 'quiet_period' : 'normal')}, 'offerings count';
    };
    subtest 'deriv_dtrader' => sub {
        my @expected_market            = qw(forex commodities indices synthetic_index);
        my @expected_contract_category = qw(callput callputequal callputspread touchnotouch multiplier);
        my @expected_underlying_symbol = qw(
            OTC_AEX
            OTC_AS51
            OTC_DJI
            OTC_FCHI
            OTC_FTSE
            OTC_GDAXI
            OTC_HSI
            OTC_IBEX35
            OTC_N225
            OTC_NDX
            OTC_SPC
            OTC_SSMI
            OTC_SX5E
            WLDAUD
            WLDEUR
            WLDGBP
            WLDUSD
            frxAUDCAD
            frxAUDCHF
            frxAUDJPY
            frxAUDNZD
            frxAUDUSD
            frxEURAUD
            frxEURCAD
            frxEURCHF
            frxEURGBP
            frxEURJPY
            frxEURNZD
            frxEURUSD
            frxGBPAUD
            frxGBPCAD
            frxGBPCHF
            frxGBPJPY
            frxGBPNZD
            frxGBPUSD
            frxNZDJPY
            frxNZDUSD
            frxUSDCAD
            frxUSDCHF
            frxUSDJPY
            frxUSDMXN
            frxUSDPLN
            frxXAGUSD
            frxXAUUSD
            frxXPDUSD
            frxXPTUSD
            WLDXAU
        );
        my $expected_count = {
            normal       => 444,
            quiet_period => 444
        };

        # Normal period
        set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
        my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('sg', $offerings_config, 'deriv_dtrader');
        is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
        is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
            'default contract_category list';
        is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
            'default underlying_symbol list';
        is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

        # Quiet period
        set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
        my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings_for_country('sg', $offerings_config, 'deriv_dtrader');
        is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
    };
};

done_testing();
