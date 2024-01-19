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

sub get_offerings {
    return LandingCompany::Offerings->get({
            filename => 'common',
            name     => 'virtual',
            config   => {
                loaded_revision         => 0,
                action                  => 'buy',
                legal_allowed_offerings => {'forex' => ['callput']}}});
}

subtest 'quiet_period' => sub {
    # for forex no ticks are offered on european hours:
    Test::MockTime::set_absolute_time('2018-10-09T09:00:00Z');
    ok !exists get_offerings()->offerings->{frxAUDJPY}{callput}{tick};

    # for forex no ticks offered on non-european hours:
    Test::MockTime::set_absolute_time('2018-10-09T02:00:00Z');
    ok !exists get_offerings()->offerings->{frxAUDJPY}{callput}{tick};

    # for frxUSDCHF 15m is offered in normal period
    Test::MockTime::set_absolute_time('2018-10-09T09:00:00Z');
    ok get_offerings()->offerings->{frxUSDCHF}{callput}{intraday}{spot}{euro_atm}{min} eq '15m';

    # for frxUSDCHF 15m is offered in quiet period
    Test::MockTime::set_absolute_time('2018-10-09T01:00:00Z');
    ok get_offerings()->offerings->{frxUSDCHF}{callput}{intraday}{spot}{euro_atm}{min} eq '15m';

};

done_testing;
