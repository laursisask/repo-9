use strict;
use warnings;
use Test::More;
use LandingCompany::Registry;
my $lc = LandingCompany::Registry->by_name('svg');

is ref $lc,         'LandingCompany::SVG', 'object of LandingCompany::SVG';
is $lc->short,      'svg',                 'short svg';
is $lc->is_eu,      '0',                   'is_eu 0';
is $lc->is_virtual, '0',                   'is_virtual 0';
is_deeply $lc->broker_codes, [qw/CR CRW/], 'broker_codes CR';

done_testing;
