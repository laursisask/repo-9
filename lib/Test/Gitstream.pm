package Test::Gitstream;
# ABSTRACT: ...

our $VERSION = '0.001';

=head1 NAME

Test::Gitstream - Module abstract

=head2 new

Constructor to initialize the class

Example:

    my $test = Test::Gitstream->new()

Does not take or return any parameters

=cut

use Object::Pad;

class Test::Gitstream;

=head2 add

Perform addition

Example:

    my $config = Test::Gitstream->new()->add(5, 10);

Return

=cut

method add ($numbers_to_Add) {
    my $sum = 0;
    foreach my $number (@$numbers_to_Add) {
        $sum += $number;
    }
    return $sum;
}

1;
