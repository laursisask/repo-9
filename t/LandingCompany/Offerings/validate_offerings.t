#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::FailWarnings;
use Test::Warnings;

use LandingCompany::Registry;

subtest 'validate_offerings' => sub {
    my $metadata = {
        underlying_symbol => 'test',
        contract_category => 'callput',
        expiry_type       => 'intraday',
        start_type        => 'spot',
        barrier_category  => 'euro_atm',
        contract_duration => 5000,
        for_sale          => 0,
        market            => 'test',
        contract_type     => 'CALL',
    };

    my $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        loaded_revision            => 0,
        action                     => 'buy',
        suspend_trading            => 0,
        suspend_markets            => [],
        suspend_contract_types     => [],
        suspend_underlying_symbols => [],
    });
    my $err = $o->validate_offerings($metadata);

    is $err->{message}, 'Invalid underlying symbol', 'error - Invalid underlying symbol';
    is_deeply $err->{message_to_client}, ['Trading is not offered for this asset.'], 'message_to_client - Trading is not offered for this asset.';

    $metadata->{underlying_symbol} = 'R_100';
    $metadata->{contract_duration} = 10;
    $metadata->{start_type}        = 'forward';
    $metadata->{expiry_type}       = 'tick';
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'trying unauthorised combination', 'error - trying unauthorised combination';
    is_deeply $err->{message_to_client}, ['Trading is not offered for this duration.'],
        'message_to_client - Trading is not offered for this duration.';

    $metadata->{start_type}        = 'spot';
    $metadata->{contract_duration} = 11;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'Invalid tick count for tick expiry', 'error - Invalid tick count for tick expiry';
    is_deeply $err->{message_to_client}, ['Number of ticks must be between [_1] and [_2].', 1, 10],
        'message_to_client - Number of ticks must be between [_1] and [_2].';

    $metadata->{expiry_type}       = 'intraday';
    $metadata->{contract_duration} = 14;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'Intraday duration not acceptable', 'error - Intraday duration not acceptable';
    is_deeply $err->{message_to_client}, ['Trading is not offered for this duration.'],
        'message_to_client - Trading is not offered for this duration.';

    $metadata->{expiry_type}       = 'daily';
    $metadata->{contract_duration} = 366;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'Daily duration is outside acceptable range', 'error - Daily duration is outside acceptable range';
    is_deeply $err->{message_to_client}, ['Trading is not offered for this duration.'],
        'message_to_client - Trading is not offered for this duration.';

    $metadata->{contract_duration} = 0;
    $metadata->{for_sale}          = 1;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'Daily duration is outside acceptable range', 'error - Daily duration is outside acceptable range';
    is_deeply $err->{message_to_client}, ['Resale of this contract is not offered.'], 'message_to_client - Resale of this contract is not offered.';

    $metadata->{contract_duration} = -1;
    $err = $o->validate_offerings($metadata);

    is $err->{message}, 'Daily duration is outside acceptable range', 'error - Daily duration is outside acceptable range';
    is_deeply $err->{message_to_client}, ['Resale of this contract is not offered.'], 'message_to_client - Resale of this contract is not offered.';

    $metadata->{contract_duration} = 10;
    $metadata->{expiry_type}       = 'tick';
    $metadata->{for_sale}          = 1;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'resale of tick expiry contract', 'error - resale of tick expiry contract';
    is_deeply $err->{message_to_client}, ['Resale of this contract is not offered.'], 'message_to_client - Resale of this contract is not offered.';

    $metadata->{contract_duration} = 10;
    $metadata->{expiry_type}       = 'intraday';
    $metadata->{for_sale}          = 1;
    $err                           = $o->validate_offerings($metadata);

    is $err->{message}, 'Intraday duration not acceptable', 'error - Intraday duration not acceptable';
    is_deeply $err->{message_to_client}, ['Resale of this contract is not offered.'], 'message_to_client - Resale of this contract is not offered.';

    $metadata->{for_sale}          = 1;
    $metadata->{contract_duration} = 16;
    $err                           = $o->validate_offerings($metadata);

    ok !$err, 'valid offerings for sale - intraday 16 seconds on R_100';

    $metadata->{contract_duration} = 15;
    $err = $o->validate_offerings($metadata);

    ok !$err, 'valid offerings for buy - intraday 15 seconds on R_100';
};

subtest 'with trading suspension' => sub {
    my $metadata = {
        underlying_symbol => 'frxUSDJPY',
        contract_category => 'callput',
        expiry_type       => 'intraday',
        start_type        => 'spot',
        barrier_category  => 'euro_atm',
        contract_duration => 5000,
        for_sale          => 0,
        market            => 'forex',
        contract_type     => 'CALL',
    };

    my $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading => 1,
        loaded_revision => rand,
        action          => 'buy',
    });
    my $err = $o->validate_offerings($metadata);
    is $err->{message}, 'Disabled platform', 'error - Disabled platform';
    is_deeply $err->{message_to_client}, ['This trade is temporarily unavailable.'], 'message_to_client - This trade is temporarily unavailable.';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading => 0,
        loaded_revision => rand,
        action          => 'buy',
    });
    $err = $o->validate_offerings($metadata);
    ok !$err, 'no error';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading            => 0,
        suspend_underlying_symbols => ['frxUSDJPY'],
        loaded_revision            => rand,
        action                     => 'buy',
    });
    $err = $o->validate_offerings($metadata);
    is $err->{message}, 'Disabled underlying_symbol', 'error - Disabled underlying_symbol';
    is_deeply $err->{message_to_client}, ['This trade is temporarily unavailable.'], 'message_to_client - This trade is temporarily unavailable.';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading            => 0,
        suspend_underlying_symbols => [],
        suspend_markets            => ['synthetic_index'],
        loaded_revision            => rand,
        action                     => 'buy',
    });
    $metadata->{underlying_symbol} = 'frxAUDJPY';
    $err = $o->validate_offerings($metadata);
    ok !$err, 'no error';

    $metadata->{market}            = 'synthetic_index';
    $metadata->{underlying_symbol} = 'R_100';
    $err                           = $o->validate_offerings($metadata);
    is $err->{message}, 'Disabled market', 'error - Disabled market';
    is_deeply $err->{message_to_client}, ['This trade is temporarily unavailable.'], 'message_to_client - This trade is temporarily unavailable.';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading            => 0,
        suspend_underlying_symbols => [],
        suspend_markets            => ['synthetic_index'],
        suspend_contract_types     => ['CALL'],
        loaded_revision            => rand,
        action                     => 'buy',
    });
    $metadata->{underlying_symbol} = 'frxAUDJPY';
    $metadata->{contract_type}     = 'CALL';
    $err                           = $o->validate_offerings($metadata);
    is $err->{message}, 'Disabled contract_type', 'error - Disabled contract_type';
    is_deeply $err->{message_to_client}, ['This trade is temporarily unavailable.'], 'message_to_client - This trade is temporarily unavailable.';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading            => 0,
        suspend_underlying_symbols => [],
        suspend_markets            => ['forex'],
        loaded_revision            => rand,
        action                     => 'buy',
    });
    $metadata->{market}            = 'synthetic_index';
    $metadata->{underlying_symbol} = 'WLDAUD';
    $err                           = $o->validate_offerings($metadata);
    ok !$err, 'no error';

    $o = LandingCompany::Registry->by_name('svg')->basic_offerings({
        suspend_trading            => 0,
        suspend_underlying_symbols => [],
        suspend_markets            => ['synthetic_index'],
        loaded_revision            => rand,
        action                     => 'buy',
    });
    $metadata->{underlying_symbol} = 'WLDAUD';
    $err = $o->validate_offerings($metadata);
    is $err->{message}, 'Disabled market', 'error - Disabled market';
    is_deeply $err->{message_to_client}, ['This trade is temporarily unavailable.'], 'message_to_client - This trade is temporarily unavailable.';
};

done_testing();
