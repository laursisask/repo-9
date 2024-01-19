use strict;
use warnings;

use Test::More;
use Test::Deep;
use Test::MockObject::Extends;
use Test::Fatal qw(lives_ok exception);
use Test::Warnings;
use LandingCompany::Registry;
subtest 'restricted_country' => sub {
    my @restricted_country_list = qw( ca py ae rw );

    # if there is no landing company specified, svg is return by default
    my $landing_company;
    my $configs = {
        'action'                     => 'buy',
        'loaded_revision'            => '1604300406.50749',
        'suspend_contract_types'     => [],
        'suspend_markets'            => [],
        'suspend_trading'            => 0,
        'suspend_underlying_symbols' => ['frxAUDPLN', 'JCI', 'frxGBPPLN', 'OTC_IBEX35']};

    lives_ok { $landing_company = LandingCompany::Registry->by_name('svg') } 'Landing company get';

    my $restricted_country_offering;
    my $allowed_country_offering;
    my $default_allowed_country = 'id';

    lives_ok { $allowed_country_offering = $landing_company->basic_offerings_for_country($default_allowed_country, $configs) }
    "Get offerings for white listed country";

    for my $restricted_country (@restricted_country_list) {
        lives_ok { $restricted_country_offering = $landing_company->basic_offerings_for_country($restricted_country, $configs) }
        "Get offerings for restricted country - $restricted_country";
        cmp_deeply($restricted_country_offering, $allowed_country_offering, "Same offering between $restricted_country and default");
    }

};

done_testing;
