#!/etc/rmg/bin/perl

use strict;
use warnings;

use Test::More tests => 3;
use Test::Deep;
use Test::Warnings;

use LandingCompany::Registry;

my @lc_check_list = sort { $a cmp $b } ('MX', 'MF', 'MFW', 'MLT');
my @all_lc        = LandingCompany::Registry->get_all;

subtest 'check if list of the landing companies that required ip check matches' => sub {
    my @lc_list = LandingCompany::Registry::get_ip_check_broker_codes();
    @lc_list = sort { $a cmp $b } @lc_list;
    cmp_deeply(\@lc_check_list, \@lc_list, "Both list matches !");
};

subtest 'check if the landing companies that required checks returns true' => sub {
    my @lc_list;
    foreach my $lc (@all_lc) {
        push @lc_list, @{$lc->{broker_codes}} if ($lc->{ip_check_required});
    }
    @lc_list = sort { $a cmp $b } @lc_list;
    cmp_deeply(\@lc_list, \@lc_check_list, "Both list matches !");
};
