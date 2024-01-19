#!/usr/bin/perl

use strict;
use warnings;

use Test::More;
use Test::FailWarnings;

use LandingCompany::Registry;
use Digest::MD5 qw(md5_hex);

subtest 'iom offerings list' => sub {
    my $iom = LandingCompany::Registry->by_name('iom')->basic_offerings({
        loaded_revision => 0,
        action          => 'buy'
    });
    my @symbols = $iom->values_for_key('underlying_symbol');
    my $hex     = md5_hex(join '', sort @symbols);
    is $hex, 'd41d8cd98f00b204e9800998ecf8427e', 'notify compliance to update RTP report for IOM';
};

subtest 'malta offerings list' => sub {
    my $iom = LandingCompany::Registry->by_name('malta')->basic_offerings({
        loaded_revision => 0,
        action          => 'buy'
    });
    my @symbols = $iom->values_for_key('underlying_symbol');
    my $hex     = md5_hex(join '', sort @symbols);
    is $hex, 'd41d8cd98f00b204e9800998ecf8427e', 'notify compliance to update RTP report for malta';
};

done_testing();
