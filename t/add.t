use strict;
use warnings;

use Test::More;
use Test::Gitstream;

my $test = Test::Gitstream->new();

subtest 'test add' => sub {
    is $test->add([10, 10]), 20, 'correct 10 + 10';
};

done_testing();
