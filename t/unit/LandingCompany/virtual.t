use strict;
use warnings;
use Test::More;
use LandingCompany::Registry;
my $lc = LandingCompany::Registry->by_name('virtual');

is ref $lc,         'LandingCompany::Virtual', 'object of LandingCompany::Virtual';
is $lc->short,      'virtual',                 'short virtual';
is $lc->is_eu,      '0',                       'is_eu 0';
is $lc->is_virtual, '1',                       'is_virtual 1';
is_deeply $lc->broker_codes, [qw/VRTC VRW/], 'broker_codes VRTC';

done_testing;
