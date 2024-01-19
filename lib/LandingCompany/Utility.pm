
package LandingCompany::Utility;

use strict;
use warnings;
use YAML::XS       qw(LoadFile);
use File::ShareDir ();
use Path::Tiny;
use Dir::Self;
use File::Spec;

## VERSION

=head1 NAME

LandingCompany::Utility - utility methods for LandingCompany modules

=head1 SYNOPSIS

    use LandingCompany::Utility;

    my $yml = LandingCompany::Utility::load_yml('landing_companies.yml');

=head1 DESCRIPTION

...

This module does not export any functions by default.

=head2 FUNCTIONS

=over 4

=item load_yml($yml_filename, @sub_dirs)

    my $all_yml = load_yml('landing_companies.yml');

...

=back

=cut

=head2 load_yml

Loads the YML file & returns config.
This subroutine makes sure that in `tests` it should look into YML file in local
repo's `share` dir instead of `cpan`.

Example usage:

    LandingCompany::Utility::load_yml(...);

Takes the following arguments as named parameters

=over 4

=item * C<yml_filename> - yml file name

=item * C<sub_dirs> - (optional) Array of Subdirectories under `Share` Dir. If not provided its assumed that file exists in `Share` dir itself.

=back

return the config loaded from yml file.

=cut

sub load_yml {
    my ($yml_filename, @sub_dirs) = @_;
    my $config = do {
        my $path = Path::Tiny::path(__DIR__)->parent(2)->child('share', @sub_dirs, $yml_filename);
        $path = Path::Tiny::path(File::ShareDir::dist_file('LandingCompany', File::Spec->catfile(@sub_dirs, $yml_filename))) unless $path->exists;
        LoadFile($path);
    };

    return $config;
}

1;
