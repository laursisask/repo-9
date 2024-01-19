#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::Exception;
use Test::Warn;
use Test::FailWarnings;
use Test::Warnings;

use LandingCompany::Commission qw(get_underlying_base_commission);

subtest 'error check' => sub {
    throws_ok { get_underlying_base_commission({}) } qr/underlying symbol is required/, 'throws error when underlying symbol is undef';
    throws_ok { get_underlying_base_commission({landing_company => 'fake', underlying_symbol => 'R_10'}) }
    qr/could not find base commission for fake/, 'throws error if landing company is not found in commission.yml';
};

subtest 'common' => sub {
    my %expected = (
        frxUSDJPY => 0.035,
        frxAUDCAD => 0.04,
        OTC_AEX   => 0.025,
        WLDUSD    => 0.035,
        frxXAUUSD => 0.05,
        R_100     => 0.012,
        frxGBPNOK => 0.05,
    );
    foreach my $s (keys %expected) {
        is get_underlying_base_commission({underlying_symbol => $s}), $expected{$s}, $s . ' base commission is ' . $expected{$s};
    }
};

done_testing();
