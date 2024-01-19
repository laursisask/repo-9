requires 'Cache::RedisDB';
requires 'DataDog::DogStatsd::Helper';
requires 'Data::Chronicle::Writer';
requires 'Date::Utility';
requires 'File::ShareDir';
requires 'Finance::Contract', '>= 0.001';
requires 'Finance::Underlying';
requires 'JSON::XS';
requires 'List::MoreUtils';
requires 'List::Util';
requires 'Locale::Country::Extra';
requires 'Memoize';
requires 'Mojo::Redis2';
requires 'Mojolicious';
requires 'Moose';
requires 'MooseX::Role::Registry', '>= 1.00';
requires 'MooseX::Singleton';
requires 'MooseX::StrictConstructor';
requires 'Time::Duration::Concise';
requires 'Time::HiRes';
requires 'URI';
requires 'YAML::XS';
requires 'indirect';
requires 'Cache::LRU';

on configure => sub {
    requires 'ExtUtils::MakeMaker', '6.64';
};

on test => sub {
    requires 'Test::More';
    requires 'Test::Warn';
    requires 'Test::FailWarnings';
    requires 'Test::Exception';
    requires 'Test::MockObject::Extends';
};
