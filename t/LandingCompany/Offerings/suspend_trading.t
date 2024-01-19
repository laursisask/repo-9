#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::FailWarnings;
use Test::Warnings;

use LandingCompany::Registry;

subtest 'disable contract-symbol combinations with config_args' => sub {
    my $time = time;
    subtest "offerings w/o arguments except for chronicles" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
            loaded_revision => 0,
            action          => 'buy'
        });
        ok $fb;
        my @list = $fb->values_for_key('underlying_symbol');
        ok scalar(@list) > 1, 'retrieved an underlying list';
    };

    subtest "suspend_trading flag is raise" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
            loaded_revision => $time++,
            action          => 'buy',
            suspend_trading => 1
        });
        my @list = $fb->values_for_key('underlying_symbol');
        ok scalar(@list) == 0, 'empty list when suspend_trading flag is raise';
    };

    subtest "frxUSDJPY is suspended" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
                loaded_revision            => $time++,
                action                     => 'buy',
                suspend_underlying_symbols => ['frxUSDJPY']});
        my %list = map { $_ => 1 } $fb->values_for_key('underlying_symbol');
        ok !$list{frxUSDJPY}, 'frxUSDJPY is excluded';
    };

    subtest "frxUSDJPY & frxAUDJPY are suspended" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
                loaded_revision            => $time++,
                action                     => 'buy',
                suspend_underlying_symbols => ['frxUSDJPY', 'frxAUDJPY']});
        my %list = map { $_ => 1 } $fb->values_for_key('underlying_symbol');
        ok !$list{frxUSDJPY}, 'frxUSDJPY is excluded';
        ok !$list{frxAUDJPY}, 'frxAUDJPY is excluded';
    };

    subtest "Forex market disabled" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
                loaded_revision => $time++,
                action          => 'buy',
                suspend_markets => ['forex']});
        my @list = $fb->query({market => 'forex'}, ['underlying_symbol']);
        ok !@list, 'no forex underlyings found if forex is disabled.';

        @list = $fb->query({market => 'indices'}, ['underlying_symbol']);
        ok @list, 'indices are still available.';
    };

    subtest "'ONETOUCH' contract type disabled" => sub {
        my $fb = LandingCompany::Registry->by_name('svg')->basic_offerings({
                loaded_revision        => $time++,
                action                 => 'buy',
                suspend_contract_types => ['ONETOUCH']});
        my %list = map { $_ => 1 } $fb->values_for_key('contract_type');
        ok !$list{ONETOUCH}, 'onetouch is disabled';
        ok $list{NOTOUCH},   'notouch is still available';

    };
};

done_testing();
