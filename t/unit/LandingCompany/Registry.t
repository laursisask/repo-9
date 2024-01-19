use strict;
use warnings;

use Test::More;
use Test::Deep;
use Test::Exception;
use Test::MockModule;

use LandingCompany::Registry;

my @all_broker_codes = LandingCompany::Registry->all_broker_codes();

subtest check_valid_broker_short_code => sub {
    ok(!LandingCompany::Registry->check_valid_broker_short_code('MX123'), 'Invalid broker code MX123');
    ok(!LandingCompany::Registry->check_valid_broker_short_code('cr'),    'Invalid broker code cr');
    ok(!LandingCompany::Registry->check_valid_broker_short_code('VRT'),   'Invalid broker code VRT');
    ok(!LandingCompany::Registry->check_valid_broker_short_code('JP'),    'Invalid broker code JP');
    ok(LandingCompany::Registry->check_valid_broker_short_code('CR'),     'Valid broker code CR');
    foreach my $broker (@all_broker_codes) {
        ok(LandingCompany::Registry->check_valid_broker_short_code($broker), "Valid broker code $broker");
    }

};

subtest check_broker_from_loginid => sub {
    ok(!LandingCompany::Registry->check_broker_from_loginid("XX12345678"), "Invalid loginid XX12345678 ");
    ok(!LandingCompany::Registry->check_broker_from_loginid("MX"),         "Invalid loginid MX");
    ok(!LandingCompany::Registry->check_broker_from_loginid("mlt123"),     "Invalid loginid mlt123 ");
    ok(LandingCompany::Registry->check_broker_from_loginid("CR123"),       "Valid loginid CR123 ");
    foreach my $broker (@all_broker_codes) {
        ok(LandingCompany::Registry->check_broker_from_loginid("${broker}12345678"), "Valid loginid ${broker}12345678");
    }
};

subtest broker_code_from_loginid => sub {
    foreach my $broker (@all_broker_codes) {
        my $code = LandingCompany::Registry->broker_code_from_loginid("${broker}12345678");
        is $code, $broker, "broker_code_from_loginid $broker";
    }
};

subtest 'aliases' => sub {
    my $lc = LandingCompany::Registry->by_name('seychelles');

    ok $lc, 'Got a Landing Company object';

    is $lc->short, 'dsl', 'Got the DSL Landing Company through its alias';

    cmp_deeply $lc->aliases, ['seychelles'], 'seychelles is an alias for dsl';

    $lc = LandingCompany::Registry->by_name('seychelles');

    ok $lc, 'Got a Landing Company object';

    is $lc->short, 'dsl', 'Got the DSL Landing Company through its alias';

    cmp_deeply $lc->aliases, ['seychelles'], 'seychelles is an alias for dsl';

    $lc = LandingCompany::Registry->by_name('dsl');

    ok $lc, 'Got a Landing Company object';

    is $lc->short, 'dsl', 'Got the DSL Landing Company through its short name';

    cmp_deeply $lc->aliases, ['seychelles'], 'seychelles is an alias for dsl';
};

done_testing;
