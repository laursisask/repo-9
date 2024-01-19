#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::FailWarnings;
use Test::Exception;
use Test::Warnings;
use YAML::XS       qw(LoadFile);
use Test::MockTime qw(set_absolute_time);
use LandingCompany::Registry;
use LandingCompany::Offerings;

subtest 'get' => sub {
    Test::MockTime::set_absolute_time('2018-10-09T08:00:00Z');
    throws_ok { LandingCompany::Offerings->get() } qr/only accept hash reference as input/, 'throws exception if nothing is passed to \'->get\'';
    throws_ok {
        LandingCompany::Offerings->get('', {loaded_revision => 0})
    }
    qr/only accept hash reference as input/, 'throws exception if input is not a hash reference';
    throws_ok {
        LandingCompany::Offerings->get({
                landing_company => 'unknown',
                config          => {
                    loaded_revision => 0,
                    action          => 'buy'
                }})
    }
    qr/name is required/, 'throws exception if there is no match';
    throws_ok {
        LandingCompany::Offerings->get({
                filename => 'unknown',
                name     => 'virtual',
            })
    }
    qr/config is undefined/, 'throws exception is config is undefined';
    throws_ok {
        LandingCompany::Offerings->get({
                filename => 'unknown',
                name     => 'virtual',
                config   => {},
            })
    }
    qr/loaded_revision is undefined/, 'throws exception is loaded_revision in config is undefined';

    isa_ok(
        LandingCompany::Offerings->get({
                filename => 'common',
                name     => 'virtual',
                config   => {
                    loaded_revision         => 0,
                    action                  => 'buy',
                    legal_allowed_offerings => {
                        'synthetic_index' => [
                            'asian',        'callput', 'callputequal', 'digits',       'endsinout', 'staysinout',
                            'touchnotouch', 'reset',   'lookback',     'highlowticks', 'runs',      'callputspread',
                            'multiplier'
                        ],
                        'indices' => [
                            'asian',        'callput', 'callputequal', 'digits',       'endsinout', 'staysinout',
                            'touchnotouch', 'reset',   'lookback',     'highlowticks', 'runs',      'callputspread',
                            'multiplier'
                        ],
                        'forex' => [
                            'asian',        'callput', 'callputequal', 'digits',       'endsinout', 'staysinout',
                            'touchnotouch', 'reset',   'lookback',     'highlowticks', 'runs',      'callputspread',
                            'multiplier'
                        ],
                        'commodities' => [
                            'asian',        'callput', 'callputequal', 'digits',       'endsinout', 'staysinout',
                            'touchnotouch', 'reset',   'lookback',     'highlowticks', 'runs',      'callputspread',
                            'multiplier'
                        ],
                    }}}
        ),
        'LandingCompany::Offerings'
    );
    my $landing_company_count = keys %{LandingCompany::Registry::get_loaded_landing_companies()};
    my $test                  = LoadFile('t/LandingCompany/Offerings/test_cases.yml');

    ok $landing_company_count == keys %$test, 'we are kind of covered';
    foreach my $short (keys %$test) {
        next unless $test->{$short};
        my $o = LandingCompany::Registry->by_name($short)->basic_offerings({
            loaded_revision => 0,
            action          => 'buy'
        });
        isa_ok($o, 'LandingCompany::Offerings');
        my @test_cases = @{$test->{$short}};
        foreach my $case (@test_cases) {
            my $got = $o->query($case->{query});
            is $got, $case->{count},
                  'offerings matches for landing company['
                . $short
                . '] with query ['
                . (join ', ', map { "$_ => $case->{query}->{$_}" } keys %{$case->{query}}) . ']';
        }
    }
};

done_testing;
