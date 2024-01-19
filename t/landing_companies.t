use strict;
use warnings;

use Test::Most 0.22;
use Test::MockModule;
use Array::Utils qw (array_minus);
use Test::Fatal  qw(lives_ok exception);

use LandingCompany::Registry;
use LandingCompany::Utility;

use constant LANDING_COMPANIES_CONFIG => {
    iom => {
        broker_code => 'MX',
        name        => 'Deriv (MX) Ltd',
        markets     => [qw(synthetic_index forex indices commodities)],
        currencies  => [qw(GBP USD)],
    },
    malta => {
        broker_code => 'MLT',
        name        => 'Deriv (Europe) Limited',
        markets     => [qw(synthetic_index)],
        currencies  => [qw(USD EUR GBP)],
    },
    maltainvest => {
        broker_code => 'MF',
        name        => 'Deriv Investments (Europe) Limited',
        markets     => [qw(forex synthetic_index cryptocurrency)],
        currencies  => [qw(USD EUR GBP)],
    },
    svg => {
        broker_code => 'CR',
        name        => 'Deriv (SVG) LLC',
        markets     => [qw(commodities forex indices synthetic_index cryptocurrency)],
        currencies  => [qw(USD EUR GBP AUD BTC LTC ETH USDC UST eUSDT tUSDT)],
    },
    virtual => {
        broker_code => 'VRTC',
        name        => 'Deriv Limited',
        markets     => [qw(commodities forex indices synthetic_index cryptocurrency)],
        currencies  => [qw(USD)],
        is_virtual  => 1,
    },
    vanuatu => {
        broker_code => '',
        name        => 'Deriv (V) Ltd',
        markets     => [qw(forex)],
        currencies  => [qw(USD)],
    },
    labuan => {
        broker_code => '',
        name        => 'Deriv (FX) Ltd',
        markets     => [qw(forex)],
        currencies  => [qw(USD)],
    },
    samoa => {
        broker_code => '',
        name        => 'Deriv Capital International Ltd',
        markets     => [],
        currencies  => [qw(USD)],
    },
    'samoa-virtual' => {
        broker_code => '',
        name        => 'Deriv Capital International Ltd (Virtual)',
        markets     => [],
        currencies  => [qw(USD)],
        is_virtual  => 1,
    },
    'bvi' => {
        broker_code => '',
        name        => 'Deriv (BVI) Ltd',
        markets     => [],
        currencies  => [qw(USD)],
    },
    'dsl' => {
        broker_code => 'CRA',
        name        => 'Deriv Services Ltd',
        markets     => [],
        currencies  => [qw(USD EUR GBP AUD)],
    },
};

use constant CURRENCIES_CONFIG => {
    USD => {
        name => 'US Dollar',
        type => 'fiat',
    },
    EUR => {
        name => 'Euro',
        type => 'fiat',
    },
    GBP => {
        name => 'Pound Sterling',
        type => 'fiat',
    },
    AUD => {
        name => 'Australian Dollar',
        type => 'fiat',
    },
    BTC => {
        name => 'Bitcoin',
        type => 'crypto',
    },
    LTC => {
        name => 'Litecoin',
        type => 'crypto',
    },
    ETH => {
        name => 'Ethereum',
        type => 'crypto',
    },
    USDC => {
        name   => 'USD Coin',
        type   => 'crypto',
        stable => 'USD',
    },
    UST => {
        name   => 'Tether Omni',
        type   => 'crypto',
        stable => 'USD',
    },
    eUSDT => {
        name   => 'Tether ERC20',
        type   => 'crypto',
        stable => 'USD',
    },
    tUSDT => {
        name   => 'Tether TRC20',
        type   => 'crypto',
        stable => 'USD',
    },
};

use constant {
    UNKNOWN_CURRENCY            => 'XXX',
    CRYPTO_ENABLED_BROKER_CODES => [qw(CR CRW)],
};

my $lc_registry;

subtest 'all landing companies' => sub {
    lives_ok { $lc_registry = 'LandingCompany::Registry'; } 'Initialized Registry';

    my @all_landing_companies  = $lc_registry->get_all;
    my @expected_lc_shortcodes = sort keys LANDING_COMPANIES_CONFIG->%*;
    my @all_currencies         = sort keys CURRENCIES_CONFIG->%*;

    cmp_bag([$lc_registry->all_currencies], [@all_currencies], 'Can get all currencies');

    is scalar @all_landing_companies, scalar keys LANDING_COMPANIES_CONFIG->%*, 'Check total number of landing companies';

    for my $short (@expected_lc_shortcodes) {
        my $expected_lc = LANDING_COMPANIES_CONFIG->{$short};
        my $name        = $expected_lc->{name};
        my $lc          = $lc_registry->by_name($short);

        subtest $short => sub {
            isa_ok $lc, 'LandingCompany';

            is $lc, $lc_registry->by_name($name), 'Got the same object by shortcode and by name';
            if (my $broker_code = $expected_lc->{broker_code}) {
                is $lc, $lc_registry->by_broker($broker_code),            'Got the same object by broker code';
                is $lc, $lc_registry->by_loginid($broker_code . '12345'), 'Got the same object by loginid';
            }

            is $lc->short,      $short,                          'Got correct shortcode';
            is $lc->name,       $name,                           'Got correct name';
            is $lc->is_virtual, $expected_lc->{is_virtual} // 0, 'Got correct virtual status';

            cmp_bag($lc->legal_allowed_markets, $expected_lc->{markets}, 'Got correct markets ' . $lc->name);

            my @currencies = sort $expected_lc->{currencies}->@*;
            for my $currency (@currencies) {
                ok $lc->is_currency_legal($currency), "$currency is legal";
                is_deeply $lc->legal_allowed_currencies->{$currency}, CURRENCIES_CONFIG->{$currency}, "$currency definition is correct";
            }
            ok !$lc->is_currency_legal($_), "$_ not legal" for (UNKNOWN_CURRENCY, array_minus(@all_currencies, @currencies));
        };
    }
};

subtest 'legal_allowed_currencies type and definition' => sub {
    for my $currency (sort keys CURRENCIES_CONFIG->%*, UNKNOWN_CURRENCY) {
        my $definition = LandingCompany::Registry::get_currency_definition($currency);
        if ($definition) {
            is_deeply $definition, CURRENCIES_CONFIG->{$currency}, "$currency definition is correct";
        } else {
            ok(!exists CURRENCIES_CONFIG->{$currency}, "No definition for unknown currency '$currency'");
        }

        my $type          = LandingCompany::Registry::get_currency_type($currency) || 'unknown';
        my $expected_type = CURRENCIES_CONFIG->{$currency}{type} // 'unknown';
        is $type, $expected_type, "$currency is $expected_type";
    }
};

subtest 'get_crypto_enabled_broker_codes' => sub {
    cmp_bag([LandingCompany::Registry::get_crypto_enabled_broker_codes()], CRYPTO_ENABLED_BROKER_CODES, 'Crypto enabled brokers are correct');
};

subtest 'china_1hz_offerings' => sub {
    my $offerings_config = {
        'loaded_revision'        => '1586757605.95497',
        'suspend_trades'         => [],
        'disabled_markets'       => ['sectors'],
        'suspend_buy'            => [],
        'suspend_contract_types' => [],
        'suspend_trading'        => '0',
        'action'                 => 'buy',
    };

    my $cr               = $lc_registry->by_name('svg');
    my $offerings_object = $cr->basic_offerings_for_country('cn', $offerings_config);

    # available contract categories for 1HZ10V
    my @actual_1HZ10V_contract_categories = $offerings_object->query({underlying_symbol => '1HZ10V'}, ['contract_category']);

    is_deeply(
        [sort(@actual_1HZ10V_contract_categories)],
        [qw[accumulator asian callput callputequal callputspread digits endsinout highlowticks lookback multiplier reset staysinout touchnotouch vanilla]],
        "China 1Hz 10V offerings contract categories"
    );

    # available contract categories for 1HZ100V
    my @actual_1HZ100V_contract_categories = $offerings_object->query({underlying_symbol => '1HZ100V'}, ['contract_category']);

    is_deeply(
        [sort(@actual_1HZ100V_contract_categories)],
        [qw[accumulator asian callput callputequal callputspread digits endsinout highlowticks lookback multiplier reset staysinout touchnotouch vanilla]],
        "China 1Hz 100V offerings contract categories"
    );
};

subtest 'disabled landing company' => sub {
    my $utility_mock = Test::MockModule->new('LandingCompany::Utility');

    subtest 'landing company is disabled' => sub {
        $utility_mock->mock(
            'load_yml' => ({
                    'dummy_landing_company' => {
                        'is_disabled' => 1,
                    }}));

        LandingCompany::Registry::load_config();
        my $loaded_landing_companies = LandingCompany::Registry->get_loaded_landing_companies();

        is scalar(keys %$loaded_landing_companies), 0, "no landing company";
        $utility_mock->unmock('load_yml');
    };

    subtest 'landing company is enabled' => sub {
        my $loaded_lcs = LandingCompany::Utility::load_yml('landing_companies.yml');
        $utility_mock->mock(
            'load_yml',
            sub {
                my $key   = (sort keys %$loaded_lcs)[0];
                my $value = $loaded_lcs->{$key};
                return {$key => $value};
            });

        LandingCompany::Registry::load_config();
        my $loaded_landing_companies = LandingCompany::Registry->get_loaded_landing_companies();

        is scalar(keys %$loaded_landing_companies), 1, 'a landing company should be available';
        $utility_mock->unmock('load_yml');
    };
};

subtest 'available_mt5_currency_group' => sub {
    # Reload landing company config.
    LandingCompany::Registry::load_config();
    my $loaded   = LandingCompany::Registry->get_loaded_landing_companies();
    my %expected = (
        virtual         => [qw(USD EUR GBP)],
        samoa           => [qw(USD EUR GBP)],
        'samoa-virtual' => [qw(USD EUR GBP)],
        svg             => ['USD'],
        malta           => ['EUR'],
        maltainvest     => [qw(EUR GBP USD)],
        iom             => [],
        labuan          => ['USD'],
        vanuatu         => ['USD'],
    );
    foreach my $lc (map { LandingCompany::Registry->by_name($_) } sort { $a cmp $b } keys %expected) {
        is_deeply $lc->available_mt5_currency_group, $expected{$lc->short}, 'available_mt5_currency_group is correct for ' . $lc->short;
    }
};

subtest 'available_trading_platform_currency_group' => sub {
    # Reload landing company config.
    LandingCompany::Registry::load_config();
    my $loaded   = LandingCompany::Registry->get_loaded_landing_companies();
    my $expected = {
        dxtrade => {
            svg         => ['USD'],
            virtual     => ['USD'],
            samoa       => [],
            malta       => [],
            maltainvest => [],
            iom         => [],
            labuan      => [],
            vanuatu     => [],
        },
        ctrader => {
            svg         => ['USD'],
            virtual     => ['USD'],
            samoa       => [],
            malta       => [],
            maltainvest => [],
            iom         => [],
            labuan      => [],
            vanuatu     => [],
        },
    };

    foreach my $trading_platform (keys $expected->%*) {
        my $companies = $expected->{$trading_platform};
        foreach my $lc (map { LandingCompany::Registry->by_name($_) } sort { $a cmp $b } keys $companies->%*) {
            is_deeply $lc->available_trading_platform_currency_group->{$trading_platform} // [], $companies->{$lc->short},
                'available_trading_platform_currency_group is correct for ' . $lc->short;
        }
    }
};

subtest 'Fully authenticated with IDV' => sub {
    my $loaded   = LandingCompany::Registry->get_loaded_landing_companies();
    my %expected = (
        svg     => [qw/idv_photo idv_address idv/],
        labuan  => [qw/idv/],
        vanuatu => [qw/idv/],
        bvi     => [qw/idv_photo idv_address idv/],
    );

    foreach my $lc (map { LandingCompany::Registry->by_name($_) } sort { $a cmp $b } keys %expected) {
        cmp_bag $lc->idv_auth_methods, $expected{$lc->short}, 'idv_auth_methods is correct for ' . $lc->short;
    }
};

subtest 'allowed POI providers' => sub {
    # Reload landing company config.
    LandingCompany::Registry::load_config();
    my $loaded   = LandingCompany::Registry->get_loaded_landing_companies();
    my %expected = (
        virtual         => [],
        samoa           => [],
        'samoa-virtual' => [],
        svg             => [qw/idv onfido manual/],
        malta           => [qw/onfido manual/],
        maltainvest     => [qw/onfido manual/],
        iom             => [qw/onfido manual/],
        labuan          => [qw/onfido manual idv/],
        vanuatu         => [qw/onfido manual idv/],
    );
    foreach my $lc (map { LandingCompany::Registry->by_name($_) } sort { $a cmp $b } keys %expected) {
        cmp_bag $lc->allowed_poi_providers, $expected{$lc->short}, 'allowed_poi_providers is correct for ' . $lc->short;
    }
};

done_testing;
