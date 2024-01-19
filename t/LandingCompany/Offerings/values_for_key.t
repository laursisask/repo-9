#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::Most;
use Test::FailWarnings;
use Test::Deep;
use Test::Exception;
use Test::Warnings;

use Finance::Contract;
use LandingCompany::Registry;

my @expected_lc = qw(virtual svg  malta iom);

subtest 'values_for_key - market' => sub {
    my %expected_market = (
        basic_offerings => {
            virtual => ['commodities', 'forex', 'indices', 'synthetic_index', 'cryptocurrency'],
            svg     => ['commodities', 'forex', 'indices', 'synthetic_index', 'cryptocurrency'],
            malta   => [],
            iom     => [],
        });

    lives_ok {
        foreach my $method (keys %expected_market) {
            foreach my $lc (@expected_lc) {
                my $fb = LandingCompany::Registry->by_name($lc)->$method({
                    loaded_revision => 0,
                    action          => 'buy'
                });
                my @market_lc = $fb->values_for_key('market');
                cmp_bag(\@market_lc, $expected_market{$method}{$lc}, 'market list for ' . $lc . ' type ' . $method);
            }
        }
    }
    'market list by landing company';

};

subtest 'values_for_key - contract_type' => sub {
    my %expected_type = (
        basic_offerings => {
            virtual => [
                'ASIAND',    'ASIANU',    'CALL',       'DIGITDIFF',   'DIGITEVEN',       'DIGITMATCH',
                'DIGITODD',  'DIGITOVER', 'DIGITUNDER', 'EXPIRYMISS',  'EXPIRYRANGE',     'NOTOUCH',
                'ONETOUCH',  'PUT',       'RANGE',      'UPORDOWN',    'LBFLOATCALL',     'LBFLOATPUT',
                'LBHIGHLOW', 'RESETCALL', 'RESETPUT',   'TICKHIGH',    'TICKLOW',         'CALLSPREAD',
                'PUTSPREAD', 'CALLE',     'PUTE',       'RUNHIGH',     'RUNLOW',          'MULTUP',
                'MULTDOWN',  'ACCU',      'TURBOSLONG', 'TURBOSSHORT', 'VANILLALONGCALL', 'VANILLALONGPUT',
            ],
            svg => [
                'ACCU', 'ASIAND',    'ASIANU',     'CALL',        'DIGITDIFF',       'DIGITEVEN',   'DIGITMATCH',
                'DIGITODD',  'DIGITOVER',  'DIGITUNDER',  'EXPIRYMISS',      'EXPIRYRANGE', 'NOTOUCH',
                'ONETOUCH',  'PUT',        'RANGE',       'UPORDOWN',        'LBFLOATCALL', 'LBFLOATPUT',
                'LBHIGHLOW', 'RESETCALL',  'RESETPUT',    'TICKHIGH',        'TICKLOW',     'CALLSPREAD',
                'PUTSPREAD', 'CALLE',      'PUTE',        'RUNHIGH',         'RUNLOW',      'MULTUP',
                'MULTDOWN',  'TURBOSLONG', 'TURBOSSHORT', 'VANILLALONGCALL', 'VANILLALONGPUT'
            ],
            malta => [],
            iom   => [],
        });
    lives_ok {
        foreach my $method (keys %expected_type) {
            foreach my $lc (@expected_lc) {
                my $lc_object = LandingCompany::Registry->by_name($lc);
                my $fb        = LandingCompany::Registry->by_name($lc)->$method({
                    loaded_revision => 0,
                    action          => 'buy'
                });
                my @type_lc = $fb->values_for_key('contract_type');
                cmp_bag(\@type_lc, $expected_type{$method}{$lc}, 'contract type list for ' . $lc . ' type ' . $method);
            }
        }
    }
    'contract list by landing company';

};

subtest 'values_fo_key - underlying_symbol' => sub {
    my @crypto      = qw(cryBTCUSD cryETHUSD cryBNBUSD cryEOSUSD cryDSHUSD cryLTCUSD cryXMRUSD cryXRPUSD cryBCHUSD cryZECUSD);
    my @random      = qw(R_75 RDBEAR RDBULL R_10 R_25 R_100 R_50 1HZ100V 1HZ10V 1HZ25V 1HZ50V 1HZ75V );
    my @crash_index = qw(CRASH1000 CRASH500 BOOM1000 BOOM500);
    my @step_index  = qw(stpRNG);
    my @non_random  = qw(
        OTC_AEX
        OTC_AS51
        OTC_FTSE
        OTC_HSI
        OTC_SSMI
        OTC_DJI
        OTC_FCHI
        OTC_GDAXI
        OTC_N225
        OTC_NDX
        OTC_SPC
        frxAUDJPY
        frxUSDJPY
        frxAUDCAD
        frxAUDNZD
        frxEURNZD
        frxUSDCAD
        frxEURAUD
        frxGBPJPY
        frxEURCHF
        frxEURJPY
        frxXPDUSD
        frxGBPUSD
        frxGBPNZD
        frxXAGUSD
        frxAUDCHF
        frxUSDPLN
        frxUSDCHF
        frxNZDJPY
        frxGBPCAD
        frxBROUSD
        frxXPTUSD
        frxUSDNOK
        frxEURCAD
        frxGBPNOK
        frxXAUUSD
        frxGBPPLN
        frxGBPAUD
        frxUSDSEK
        frxUSDMXN
        frxAUDUSD
        frxGBPCHF
        frxEURUSD
        frxEURGBP
        frxNZDUSD
        OTC_IBEX35
        OTC_SX5E
    );
    my @forex_basket     = qw(WLDAUD WLDEUR WLDUSD WLDGBP);
    my @commodity_basket = ('WLDXAU',);
    my @jump_index       = ('JD10', 'JD100', 'JD25', 'JD50', 'JD75');
    my %expected_list    = (
        basic_offerings => {
            malta => [],
            iom   => [],
            svg   => [@random, @non_random, @forex_basket, @commodity_basket, @crash_index, @step_index, @crypto, @jump_index],
        });

    foreach my $method (keys %expected_list) {
        foreach my $lc (keys %{$expected_list{$method}}) {
            my @got = LandingCompany::Registry->by_name($lc)->$method({
                    loaded_revision => 0,
                    action          => 'buy'
                })->values_for_key('underlying_symbol');
            cmp_bag(\@got, $expected_list{$method}{$lc}, 'underlying list for ' . $lc . ' type ' . $method);
        }
    }
};

subtest 'values_for_key - barrier_category' => sub {
    my %expected      = %{$Finance::Contract::BARRIER_CATEGORIES};
    my $offerings_obj = LandingCompany::Registry->by_name('virtual')->basic_offerings({
        loaded_revision => 0,
        action          => 'buy'
    });
    # For basic offering, we do not want to offer euro_non_atm for callputequal because we want it to contiue offers under multibarrier

    $expected{callputequal} = ['euro_atm'];
    eq_or_diff(
        [sort($offerings_obj->values_for_key('contract_category'))],
        [sort keys %expected],
        'Expectations set for all available contract categories'
    );

    $offerings_obj = LandingCompany::Registry->by_name('svg')->basic_offerings({
        loaded_revision => 0,
        action          => 'buy'
    });

    eq_or_diff(
        [sort($offerings_obj->values_for_key('contract_category'))],
        [sort keys %expected],
        'Expectations set for all available contract categories'
    );

    while (my ($cc, $hoped) = each(%expected)) {
        cmp_bag([sort($offerings_obj->query({contract_category => $cc}, ['barrier_category']))], $hoped, '... ' . $cc . ' meets expectations');
    }
};

done_testing;
