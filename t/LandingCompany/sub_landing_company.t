use strict;
use warnings;
use Test::More;
use LandingCompany::Registry;

my %name_to_class = (
    'bvi'           => 'BVI',
    'dsl'           => 'DSL',
    'iom'           => 'IOM',
    'labuan'        => 'Labuan',
    'malta'         => 'Malta',
    'maltainvest'   => 'MaltaInvest',
    'samoa'         => 'Samoa',
    'samoa-virtual' => 'SamoaVirtual',
    'svg'           => 'SVG',
    'vanuatu'       => 'Vanuatu',
    'virtual'       => 'Virtual',
);

subtest 'get sub LandingCompany' => sub {
    my $lc = LandingCompany::Registry->by_name('svg');
    is ref $lc, 'LandingCompany::SVG', 'by_name ok';

    $lc = LandingCompany::Registry->by_broker('CR');
    is ref $lc, 'LandingCompany::SVG', 'by_broker ok';

    $lc = LandingCompany::Registry->by_loginid('CR12345');
    is ref $lc, 'LandingCompany::SVG', 'by_loginid CR ok';

    $lc = LandingCompany::Registry->by_loginid('MX12345');
    is ref $lc, 'LandingCompany::IOM', 'by_loginid MX ok';

    my $sublc = LandingCompany::Registry->get_default_company();
    is ref $sublc, 'LandingCompany::Virtual', 'get_default_company ok';
    ok $sublc->is_virtual, 'default is_virtual';
};

subtest 'get all LandingCompany' => sub {
    my @get_all = LandingCompany::Registry->get_all();
    foreach my $sublc (@get_all) {
        my $class = ref $sublc;
        $class = $sublc->short . " => $class";
        ok $name_to_class{$sublc->short}, "get_all: " . $sublc->short;
    }

};

subtest 'get by_broker' => sub {
    my @all_broker_codes = LandingCompany::Registry->all_broker_codes();

    foreach my $broker (@all_broker_codes) {
        my $sublc = LandingCompany::Registry->by_broker($broker);
        isa_ok $sublc, 'LandingCompany';
    }
};

subtest 'validate each get sub LandingCompany' => sub {
    foreach my $name (keys %name_to_class) {
        my $sublc = LandingCompany::Registry->by_name($name);
        my $class = ref $sublc;
        is $class, "LandingCompany::" . $name_to_class{$name}, "$class ok";
    }
};

done_testing;
