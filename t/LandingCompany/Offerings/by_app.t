#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::Deep;
use Test::FailWarnings;

use Test::MockTime qw(set_absolute_time);
use Date::Utility;
use LandingCompany::Registry;

my $offerings_config = {
    action          => 'buy',
    loaded_revision => 1,
};

subtest 'default offerings' => sub {
    my @expected_market = qw(forex commodities synthetic_index cryptocurrency indices);
    my @expected_contract_category =
        qw(callput callputequal callputspread digits runs touchnotouch endsinout staysinout lookback multiplier highlowticks accumulator asian reset vanilla turbos);
    my @expected_underlying_symbol = qw(
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
        BOOM1000
        BOOM500
        CRASH1000
        CRASH500
        JD10
        JD100
        JD25
        JD50
        JD75
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
        WLDAUD
        WLDEUR
        WLDGBP
        WLDUSD
        WLDXAU
        cryBCHUSD
        cryBNBUSD
        cryBTCUSD
        cryDSHUSD
        cryEOSUSD
        cryETHUSD
        cryLTCUSD
        cryXMRUSD
        cryXRPUSD
        cryZECUSD
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
        stpRNG);
    my $expected_count = {
        normal       => 1686,
        quiet_period => 1686,
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config);
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config);
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

subtest 'svg + binary_smarttrader' => sub {
    my @expected_market            = qw(forex commodities synthetic_index indices);
    my @expected_contract_category = qw(callput callputequal digits runs touchnotouch endsinout staysinout lookback highlowticks asian reset);
    my @expected_underlying_symbol = qw(
        JD10
        JD100
        JD25
        JD50
        JD75
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
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
        frxXPTUSD);
    my $expected_count = {
        normal       => 1348,
        quiet_period => 1348,
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_smarttrader');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_smarttrader');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

subtest 'svg + binary_ticktrade' => sub {
    my @expected_market            = qw(synthetic_index);
    my @expected_contract_category = qw(callput digits highlowticks asian);
    my @expected_underlying_symbol = qw(
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
        JD10
        JD100
        JD25
        JD50
        JD75
    );

    my $expected_count = {
        normal       => 200,
        quiet_period => 200,
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_ticktrade');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_ticktrade');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
    is_deeply [sort $offerings_quite_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
};

subtest 'svg + binary_webtrader' => sub {
    my @expected_market            = qw(forex commodities synthetic_index indices);
    my @expected_contract_category = qw(callput callputequal digits touchnotouch endsinout staysinout lookback asian);
    my @expected_underlying_symbol = qw(
        JD10
        JD100
        JD25
        JD50
        JD75
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
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
        frxXPTUSD);
    my $expected_count = {
        normal       => 1268,
        quiet_period => 1268,
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_webtrader');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_webtrader');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

subtest 'svg + binary_bot' => sub {
    my @expected_market            = qw(forex commodities synthetic_index indices);
    my @expected_contract_category = qw(callput callputequal digits runs touchnotouch endsinout staysinout highlowticks asian reset);
    my @expected_underlying_symbol = qw(
        JD10
        JD100
        JD25
        JD50
        JD75
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
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
        frxXPTUSD);
    my $expected_count = {
        normal       => 1318,
        quiet_period => 1318
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_bot');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'binary_bot');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

subtest 'svg + deriv_dtrader' => sub {
    my @expected_market            = qw(forex commodities synthetic_index indices cryptocurrency);
    my @expected_contract_category = qw(accumulator callput callputequal callputspread digits touchnotouch multiplier vanilla turbos);
    my @expected_underlying_symbol = qw(
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
        BOOM1000
        BOOM500
        CRASH1000
        CRASH500
        JD10
        JD100
        JD25
        JD50
        JD75
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
        WLDAUD
        WLDEUR
        WLDGBP
        WLDUSD
        WLDXAU
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
        stpRNG
        cryBCHUSD
        cryBNBUSD
        cryBTCUSD
        cryDSHUSD
        cryEOSUSD
        cryETHUSD
        cryLTCUSD
        cryXMRUSD
        cryXRPUSD
        cryZECUSD);
    my $expected_count = {
        normal       => 1136,
        quiet_period => 1136
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'deriv_dtrader');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'deriv_dtrader');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

subtest 'svg + deriv_go' => sub {
    my $o                          = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'deriv_go');
    my @expected_market            = qw(forex commodities synthetic_index indices cryptocurrency);
    my @expected_contract_category = qw(callputspread multiplier callput callputequal);
    my @expected_underlying_symbol = qw(
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
        BOOM1000
        BOOM500
        CRASH1000
        CRASH500
        JD10
        JD100
        JD25
        JD50
        JD75
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
        WLDAUD
        WLDEUR
        WLDGBP
        WLDUSD
        WLDXAU
        cryBCHUSD
        cryBNBUSD
        cryBTCUSD
        cryDSHUSD
        cryEOSUSD
        cryETHUSD
        cryLTCUSD
        cryXMRUSD
        cryXRPUSD
        cryZECUSD
        frxAUDCAD
        frxAUDJPY
        frxAUDCHF
        frxAUDNZD
        frxAUDUSD
        frxBROUSD
        frxXAGUSD
        frxXAUUSD
        frxXPDUSD
        frxXPTUSD
        frxEURAUD
        frxEURCAD
        frxEURCHF
        frxEURGBP
        frxEURJPY
        frxEURUSD
        frxEURNZD
        frxGBPAUD
        frxGBPCAD
        frxGBPCHF
        frxGBPJPY
        frxGBPNOK
        frxGBPPLN
        frxGBPNZD
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
        stpRNG);
    is_deeply [sort $o->values_for_key('market')],            [sort @expected_market],            'default market list';
    is_deeply [sort $o->values_for_key('contract_category')], [sort @expected_contract_category], 'default contract_category list';
    is_deeply [sort $o->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol], 'default underlying_symbol list';
    my $expected_count = 976;
    is $o->query({}), $expected_count, 'offerings count';
};

subtest 'svg + deriv_bot' => sub {
    my @expected_market            = qw(forex commodities synthetic_index indices);
    my @expected_contract_category = qw(callput callputequal digits runs touchnotouch endsinout staysinout highlowticks asian reset multiplier);
    my @expected_underlying_symbol = qw(
        JD10
        JD100
        JD25
        JD50
        JD75
        BOOM1000
        BOOM500
        CRASH1000
        CRASH500
        1HZ100V
        1HZ10V
        1HZ25V
        1HZ50V
        1HZ75V
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
        RDBEAR
        RDBULL
        R_10
        R_100
        R_25
        R_50
        R_75
        WLDAUD
        WLDEUR
        WLDGBP
        WLDUSD
        WLDXAU
        stpRNG
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
        frxAUDCAD);
    my $expected_count = {
        normal       => 1416,
        quiet_period => 1416
    };

    set_absolute_time(Date::Utility->new('2021-10-11 10:20:00')->epoch);
    my $offerings_normal_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'deriv_bot');
    is_deeply [sort $offerings_normal_period->values_for_key('market')], [sort @expected_market], 'default market list';
    is_deeply [sort $offerings_normal_period->values_for_key('contract_category')], [sort @expected_contract_category],
        'default contract_category list';
    is_deeply [sort $offerings_normal_period->values_for_key('underlying_symbol')], [sort @expected_underlying_symbol],
        'default underlying_symbol list';
    is $offerings_normal_period->query({}), $expected_count->{'normal'}, 'offerings count';

    set_absolute_time(Date::Utility->new('2021-10-11 01:20:00')->epoch);
    my $offerings_quite_period = LandingCompany::Registry->by_name('svg')->basic_offerings($offerings_config, 'deriv_bot');
    is $offerings_quite_period->query({}), $expected_count->{'quiet_period'}, 'offerings count';
};

done_testing();
