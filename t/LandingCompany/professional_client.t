#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 2;
use Test::Deep;
use Test::Warnings;

use LandingCompany::Registry;

my @lc_with_professional_support = qw(MF MFW);
my @all_lc                       = LandingCompany::Registry->get_all;

subtest 'check if the landing companies that required checks returns true' => sub {
    my @lc_list;
    my @lc_not_supported_list;

    foreach my $lc (@all_lc) {
        $lc->{support_professional_client} ? push @lc_list, @{$lc->{broker_codes}} : push @lc_not_supported_list, @{$lc->{broker_codes}};
    }

    cmp_deeply(\@lc_list, bag(@lc_with_professional_support), "Supported list matches !");

    cmp_deeply(\@lc_not_supported_list, bag(qw(MLT MX CR VRTC CRA CRW VRW)), "Unsupported list matches !");
};
