package LandingCompany::Offerings;

use Moose;

use Finance::Underlying;
use Finance::Contract::Category;
use List::Util     qw(uniq);
use YAML::XS       qw(LoadFile);
use File::ShareDir ();
use Time::Duration::Concise;
use Cache::LRU;
use Date::Utility;
use Storable qw(dclone);
use LandingCompany::Utility;
## VERSION

=head1 NAME

LandingCompany::Offerings - represents contract offerings for binary.com

=head1 USAGE

    use LandingCompany::Offerings;

    my $config = {
        suspend_underlying_symbols      => ['frxUSDJPY'],
        suspend_markets => [],
        suspend_trading => 0,
    };

    my $offerings_obj = LandingCompany::Offerings->get('common', $config);
    $offerings_obj->values_for_key('underlying_symbol'); # returns all available underlying symbols
    $offerings_obj->query({market => 'forex'}, ['contract_type']); # returns all available contract types for forex market
    $offerings_obj->query({market => 'forex'}); # returns all offerings for forex market

=cut

# since offerings are pretty much static and defined in its own yaml files,
# we are caching the objects here until the yaml file or config revision changes.
my $_cache = Cache::LRU->new(size => 500);

my %error_mapping = (
    TradeTemporarilyUnavailable => 'This trade is temporarily unavailable.',
    UnderlyingNotOffered        => 'Trading is not offered for this asset.',
    ResaleNotOffered            => 'Resale of this contract is not offered.',
    TradingDurationNotAllowed   => 'Trading is not offered for this duration.',
    TicksNumberLimits           => 'Number of ticks must be between [_1] and [_2].',
    SelectedTickNumberLimits    => 'Number of ticks must be [_1].',
);

my %application = map {
    my ($brand, $app_filename) = $_ =~ /^(binary|deriv)_(.*)$/;
    $_ => LandingCompany::Utility::load_yml($app_filename . '.yml', ('offerings', 'app', $brand))
} qw(deriv_bot deriv_dtrader deriv_go deriv_smarttrader deriv_binarybot binary_smarttrader binary_ticktrade binary_webtrader binary_bot);

# default app with everything
$application{default} = LandingCompany::Utility::load_yml('default.yml', ('offerings', 'app'));

my %available_offerings =
    map { $_ => LandingCompany::Utility::load_yml($_ . '.yml', ('offerings', 'basic')) }
    qw(china volatility_non_eu common common_eu volatility_eu financial financial_multiplier smartfx_multiplier crypto_multiplier volatility_eu_low_leverage volatility_eu_low_leverage_row crashboom_multiplier internal_launch);

# define no offerings here
$available_offerings{none} = {};

# common and financial have a correspondig quiet_period config
my $available_offerings_quiet_period = LandingCompany::Utility::load_yml('quiet_period.yml', ('offerings', 'basic'));

my %supported_types = map { $_ => 1 }
    qw(ASIANU ASIAND CALL PUT DIGITDIFF DIGITMATCH DIGITOVER DIGITUNDER DIGITEVEN DIGITODD EXPIRYMISS EXPIRYRANGE RANGE UPORDOWN ONETOUCH NOTOUCH LBFLOATCALL LBFLOATPUT LBHIGHLOW RESETCALL RESETPUT TICKHIGH TICKLOW CALLSPREAD PUTSPREAD CALLE PUTE RUNHIGH RUNLOW MULTUP MULTDOWN ACCU TURBOSLONG TURBOSSHORT VANILLALONGCALL VANILLALONGPUT);

=head2 name

name of offerings.

=head2 filename

filename of the offerings file to load.

=head2 config

The filter config

=head2 offerings

A hash reference of underlying_symbol-offerings loaded from the yaml file.

=head2 is_quiet_period

A boolean to distinguish offerings during a quiet period.

=cut

=head2 application

Whitelisted application offerings definition.

=cut

sub application {
    return \%application;
}

sub available_offerings {
    return \%available_offerings;
}

sub available_offerings_quiet_period {
    return $available_offerings_quiet_period;
}

=head2 is_asian_hours

Flag to determine whether we are in quiet period which will have limited trade

=cut

sub is_asian_hours {
    my $self   = shift;
    my $period = shift;

    my $from = $period->{non_dst}{from};
    my $to   = $period->{non_dst}{to};

    my $d = Date::Utility->new;

    # adjust period for dst
    if ($d->is_dst_in_zone('Europe/London')) {
        $from = $period->{dst}{from};
        $to   = $period->{dst}{to};
    }

    my $hour = $d->hour;
    return 1 if $hour >= $from && $hour < $to;

    return 0;
}

has [qw(name filename config offerings)] => (
    is       => 'ro',
    required => 1,
);

has is_quiet_period => (
    is      => 'ro',
    default => 0,
);

=head2 supported_contract_types

A hash reference of supported contract types for this offerings.

=cut

has supported_contract_types => (
    is      => 'ro',
    default => sub { return \%supported_types },
);

=head2 all_records

All offerings records for a country or landing company

=cut

has [qw(all_records records_by_underlying_symbol)] => (
    is         => 'ro',
    lazy_build => 1,
);

sub _build_records_by_underlying_symbol {
    my $self = shift;

    my $offerings = $self->offerings;
    my $config    = $self->config;

    return {} if $config->{suspend_trading};

    my $app_offerings = $config->{app_offerings}->{available_offerings};
    my %app_contract_category;
    foreach my $app_market (keys %$app_offerings) {
        my %cc = map { $_ => 1 } @{$app_offerings->{$app_market}};
        $app_contract_category{$app_market} = \%cc;
    }
    # There are many levels in offerings where you could offer a subset of USDJPY on callput by applying filter.
    # Applicable filters are:
    # - start_type
    # - expiry_type
    # - barrier_category
    # - underlying_symbol
    my $app_filter               = $config->{app_offerings}->{suspend};
    my $contract_category_config = Finance::Contract::Category::get_all_contract_categories();
    my $contract_type_config     = Finance::Contract::Category::get_all_contract_types();
    my $records                  = {};

    foreach my $underlying_symbol (sort keys %$offerings) {
        next if $config->{suspend_underlying_symbols}->{$underlying_symbol};

        my $ul = Finance::Underlying->by_symbol($underlying_symbol);

        next if $app_filter->{underlying_symbol} and $app_filter->{underlying_symbol}{$underlying_symbol};
        next if $config->{suspend_markets}->{$ul->market};
        next unless $config->{legal_allowed_offerings}->{$ul->market} and $app_offerings->{$ul->market};
        my %legal_allowed_contract_categories =
            map { $_ => 1 } grep { $app_contract_category{$ul->market}{$_} } @{$config->{legal_allowed_offerings}->{$ul->market}};

        my %record = (
            market            => $ul->market,
            submarket         => $ul->submarket,
            underlying_symbol => $ul->symbol,
            exchange_name     => $ul->exchange_name,
        );
        foreach my $cc_code (sort keys %{$offerings->{$underlying_symbol}}) {
            next unless $legal_allowed_contract_categories{$cc_code};
            $record{contract_category} = $cc_code;
            my $category = $contract_category_config->{$cc_code};
            $record{contract_category_display} = $category->{display_name};
            foreach my $expiry_type (sort keys %{$offerings->{$underlying_symbol}{$cc_code}}) {
                next if $app_filter->{expiry_type} and $app_filter->{expiry_type}{$expiry_type};
                $record{expiry_type} = $expiry_type;
                foreach my $start_type (sort keys %{$offerings->{$underlying_symbol}{$cc_code}{$expiry_type}}) {
                    next if $app_filter->{start_type} and $app_filter->{start_type}{$start_type};
                    $record{start_type} = $start_type;
                    foreach my $barrier_category (sort keys %{$offerings->{$underlying_symbol}{$cc_code}{$expiry_type}{$start_type}}) {
                        next if $app_filter->{barrier_category} and $app_filter->{barrier_category}{$barrier_category};
                        $record{barrier_category} = $barrier_category;
                        $record{min_contract_duration} =
                            $offerings->{$underlying_symbol}{$cc_code}{$expiry_type}{$start_type}{$barrier_category}{min};
                        $record{max_contract_duration} =
                            $offerings->{$underlying_symbol}{$cc_code}{$expiry_type}{$start_type}{$barrier_category}{max};
                        foreach my $contract_type (@{$category->{available_types}}) {
                            next unless $self->supported_contract_types->{$contract_type};
                            next if $config->{suspend_contract_types}->{$contract_type};
                            $record{sentiment}        = $contract_type_config->{$contract_type}{sentiment};
                            $record{contract_display} = $contract_type_config->{$contract_type}{display_name};
                            $record{contract_type}    = $contract_type;
                            #Note that we cannot just pass a reference here
                            push @{$records->{$underlying_symbol}}, {%record};
                        }
                    }
                }
            }
        }
    }

    return $records;
}

sub _build_all_records {
    my $self = shift;

    return [map { @$_ } values %{$self->records_by_underlying_symbol}];
}

=head2 get

Get BOM::Product::Offerings object for a country or a landing company.

->get({landing_company => 'common', config => {loaded_revision => 0}});
->get({country => 'china', config => {loaded_revision => 0}});

=cut

sub get {
    my ($class, $args) = @_;

    die '->get() only accept hash reference as input.' if (not $args or ref($args) ne 'HASH');
    die "name is required."     unless $args->{name};
    die "filename is required." unless $args->{filename};

    my $config = $args->{config};
    die 'config is undefined'                  unless $config;
    die 'loaded_revision is undefined'         unless exists $config->{loaded_revision};
    die 'action is undefined'                  unless $config->{action};
    die 'legal_allowed_offerings is undefined' unless $config->{legal_allowed_offerings};

    # the offerings file to load
    my $filename = (ref $args->{filename} eq 'ARRAY') ? $args->{filename} : [$args->{filename}];
    my $app      = $args->{app} // 'default';
    # $name format
    # - svg ($landing_company_short)
    # - svg_id ($landing_company_short, $country_code)
    my $name = lc $args->{name};

    my $asian_hours           = '';
    my $quiet_period_offering = undef;
    my $quiet_period_all      = _combine_offerings($class->available_offerings_quiet_period, $filename);
    # consider asian hours only if there is a correspondig quiet period config
    if (defined $quiet_period_all) {
        for my $key (keys $quiet_period_all->%*) {
            my $offering_period = $quiet_period_all->{$key};
            if ($class->is_asian_hours($offering_period->{period})) {
                $quiet_period_offering = $offering_period->{offerings};
                $asian_hours           = '_asian_hour_' . $key;
            }
        }
    }

    my $cache_key = join '_', ($name . $asian_hours, $app, $config->{action}, $config->{loaded_revision});
    if (my $d = $_cache->get($cache_key)) {
        return $d;
    }

    # create an empty offerings object so that we don't have to check if the object is defined
    # in every use case.
    my $offerings = _combine_offerings($class->available_offerings, $filename);
    die 'offerings not found for filename[' . $filename . '] class[' . $class . ']' unless $offerings;

    if ($asian_hours) {
        $offerings = dclone($offerings);
        foreach my $underlying (keys %{$quiet_period_offering}) {
            if (defined $offerings->{$underlying}) {
                # This delete operation might look superfluous but it's not. The
                # offerings object is created using YAML::XS::LoadFile from YAML
                # content that looks similar to this:
                #
                #   ---
                #   a: &ab
                #     k: v
                #   b: *ab
                #
                # This creates a hash with 2 keys, "a" and "b". The value of "a"
                # is again a hash with a key "k" and a value "v". The value of
                # "b" in the outer hash is then the SAME as the value of key "a".
                # To express the same in Perl you need the an experimental feature
                # introduced in 5.22:
                #
                #   use 5.022;
                #   use feature qw/refaliasing/;
                #   no warnings qw/experimental::refaliasing/;
                #   my $h = {a=>{qw/k v/}};       # prepare a hash {k=>"v"} and assing it to key "a"
                #   \$h->{b}=\$h->{a};            # this is the trick that tells Perl that "b" is the SAME as "a"
                #   print $h->{a}->{k}, "\n";     # this prints "v", as expected
                #   $h->{b}={k=>19};              # now we assign to the key "b"
                #   print $h->{a}->{k}, "\n";     # and it magically changes what we see under key "a"
                #
                # For more information see https://metacpan.org/pod/perlref#Assigning-to-References
                #
                # By deleting the element first the magic is removed.
                delete $offerings->{$underlying};

                $offerings->{$underlying} = $quiet_period_offering->{$underlying};
            }
        }
    }

    my $app_offerings = $class->application->{$app};
    my $pretty_config = {
        suspend_trading            => $config->{suspend_trading},
        suspend_underlying_symbols => +{map { $_ => 1 } @{$config->{suspend_underlying_symbols} // []}},    # list of underlying symbols
        suspend_markets            => +{map { $_ => 1 } @{$config->{suspend_markets}            // []}},    # list of market names
        suspend_contract_types     => +{map { $_ => 1 } @{$config->{suspend_contract_types}     // []}},    # a list of contract types
        legal_allowed_offerings    => $config->{legal_allowed_offerings},    # a list of market-contract_categories allowed by landing company
        app_offerings              => $app_offerings,
    };

    my $new_offerings = $class->new(
        name            => $name,
        filename        => $filename,
        config          => $pretty_config,
        offerings       => $offerings,
        is_quiet_period => $asian_hours ? 1 : 0,
    );

    $_cache->set($cache_key => $new_offerings);

    return $new_offerings;
}

=head2 query

    We look through all hashes and find those, who fits into $query hashref. Every key of %$query is either
    value itself, or array of all possible values(OR-ed).

    After query, we either return new array with values, or, if $return is defined - array of arrayrefs(if
    @$return has multiple key) or values (it only one key) with values with the same order, as keys were.

    Return values is array

=cut

sub query {
    my ($self, $query, $return) = @_;

    die "unsupported query: $query" unless ref $query eq 'HASH';
    my $result =
        $query->{underlying_symbol} ? [@{$self->records_by_underlying_symbol->{$query->{underlying_symbol}} // []}] : [@{$self->all_records}];

    for my $k (keys %$query) {
        my $v = $query->{$k};
        next unless defined $v;
        if (ref $v eq 'ARRAY') {
            my $tr = [];
            foreach my $val (@$v) {
                push @$tr, grep { defined $_->{$k} and $_->{$k} eq $val } @$result;
            }
            $result = $tr;
        } else {
            $result = [grep { defined $_->{$k} and $_->{$k} eq $v } @$result];
        }
    }
    if ($return) {
        my $seen       = {};
        my $new_result = [];
        $return = [$return] if ref($return) ne 'ARRAY';
        my $key_count = scalar @$return;
        foreach my $i (@$result) {
            my @element  = map { ($i->{$_} // '') } @$return;
            my $seen_key = join('->', @element);
            if (not $seen->{$seen_key}) {
                push @$new_result, $key_count > 1 ? \@element : $element[0];
                $seen->{$seen_key}++;
            }
        }
        $result = $new_result;
    } else {
        $result = [map { ; +{%$_} } @$result];
    }

    return @$result;
}

=head2 validate_offerings

Returns a hash reference with 'message' and 'message_to_client' if no match is found for the request key-value pair.

->validate_offerings({
    underlying_symbol => 'frxUSDJPY',
    barrier_category  => 'euro_atm',
    contract_category => 'callput',
    contract_type     => 'CALL',
    start_type        => 'spot',
    expiry_type       => 'intraday',
    for_sale          => 0,
    contract_duration => 600, # 600 seconds, for expiry_type=daily, contract_duration is the number of days, for expiry_type=tick, contract duration is number of ticks
});

=cut

sub validate_offerings {
    my ($self, $metadata) = @_;

    unless ($self->offerings->{$metadata->{underlying_symbol}}) {
        return {
            message           => 'Invalid underlying symbol',
            message_to_client => [$error_mapping{UnderlyingNotOffered}],
            details           => {field => 'symbol'},
        };
    }

    unless ($self->offerings->{$metadata->{underlying_symbol}}->{$metadata->{contract_category}}) {
        return {
            message           => 'Invalid contract category',
            message_to_client => [$error_mapping{UnderlyingNotOffered}],
            details           => {field => 'contract_category'},
        };
    }

    # if the combination exists in the offerings yaml, then we must have disabled it
    if (my $what = $self->is_disabled($metadata)) {
        return {
            message           => 'Disabled ' . $what,
            message_to_client => [$metadata->{for_sale} ? $error_mapping{ResaleNotOffered} : $error_mapping{TradeTemporarilyUnavailable}],
            details           => {field => $what},
        };
    }

    my $contract_duration = $metadata->{contract_duration};
    my $for_sale          = $metadata->{for_sale};
    my $contract_category = $metadata->{contract_category};
    my $expiry_type       = $metadata->{expiry_type};
    my $message_to_client =
        $for_sale
        ? [$error_mapping{ResaleNotOffered}]
        : [$error_mapping{TradingDurationNotAllowed}];

    if ($expiry_type eq 'tick' && $for_sale) {
        # we don't offer sellback on tick expiry contracts.
        return {
            message           => 'resale of tick expiry contract',
            message_to_client => $message_to_client,
        };
    }

    if (($contract_category eq 'reset') && $for_sale) {
        # we don't offer sellback on reset contracts.
        return {
            message           => 'resale of reset contract',
            message_to_client => $message_to_client,
        };
    }

    my $message =
          $expiry_type eq 'tick'     ? 'Invalid tick count for tick expiry'
        : $expiry_type eq 'intraday' ? 'Intraday duration not acceptable'
        :                              'Daily duration is outside acceptable range';

    # We could have use ->query($metadata, ['min_contract_duration', 'max_contract_duration']).
    # But if we are looking for something specific, it is faster to look directly in the file.
    my %query_args = map { $_ => $metadata->{$_} } qw(underlying_symbol contract_category start_type expiry_type barrier_category contract_type);
    my @permitted  = $self->query(\%query_args, ['min_contract_duration', 'max_contract_duration']);

    # This might be empty because we don't have short-term expiries on some contracts, even though
    # it's a valid bet type for multi-day contracts.
    unless (@permitted) {
        return {
            message           => 'trying unauthorised combination',
            message_to_client => $message_to_client,
            $for_sale ? () : (details => {field => 'duration'}),
        };
    }

    my ($min, $max) = (0, 0);
    if ($expiry_type eq 'no_expiry') {
        # duration is not applicable for this contract.
        return undef;
    } elsif ($expiry_type eq 'tick') {
        ($min, $max) = @{$permitted[0]};

        if ($contract_duration < $min || $contract_duration > $max) {
            my $tick_error_mapping =
                $min == $max ? [$error_mapping{SelectedTickNumberLimits}, $min] : [$error_mapping{TicksNumberLimits}, $min, $max];
            return {
                message           => $message,
                message_to_client => $tick_error_mapping,
                details           => {field => 'duration'},
            };
        }
    } else {
        my ($min, $max) =
            map { my $ti = Time::Duration::Concise->new(interval => $_); $expiry_type eq 'daily' ? $ti->days : $ti->seconds } (@{$permitted[0]});

        if ($contract_duration < $min || $contract_duration > $max) {
            return {
                message           => $message,
                message_to_client => $message_to_client,
                details           => {field => 'duration'},
            };
        }
    }

    return;
}

sub is_disabled {
    my ($self, $metadata) = @_;

    my $config = $self->config;

    if ($config->{suspend_trading}) {
        return 'platform';
    }

    if ($config->{suspend_contract_types} and $config->{suspend_contract_types}->{$metadata->{contract_type}}) {
        return 'contract_type';
    }

    if ($config->{suspend_markets} and $config->{suspend_markets}->{$metadata->{market}}) {
        return 'market';
    }

    if ($config->{suspend_underlying_symbols} and $config->{suspend_underlying_symbols}->{$metadata->{underlying_symbol}}) {
        return 'underlying_symbol';
    }

    return;
}

=head2 values_for_key

 Here we return all possible values of key inside our array, sorted

=cut

sub values_for_key {
    my ($self, $key) = @_;
    return (sort keys %{$self->records_by_underlying_symbol}) if $key eq 'underlying_symbol';
    return (sort grep { defined } uniq map { $_->{$key} } @{$self->all_records});
}

#
# two following functions are used only in tests
#

=head2 records

Returns arrayref of records

=cut

sub records {
    my $self = shift;
    return $self->all_records;
}

=head2 all_keys

Returns an array with all known keys against which one might query.

=cut

sub all_keys {
    my $self   = shift;
    my @values = uniq map { keys %$_ } @{$self->all_records};
    return (sort @values);
}

=head2 add_recods

add provided elements to the object

=cut

sub add_records {
    my $self = shift;

    return push @{$self->all_records}, @_;
}

## PRIVATE METHODS ##

=head2 _combine_offerings

Combine offerings config based on filename.

If there's conflicting offerings definition, the latter will override the former

=cut

sub _combine_offerings {
    my ($source, $filename) = @_;

    my %offerings = map { %{$source->{$_}} } grep { $source->{$_} } @$filename;

    return \%offerings;
}

no Moose;
__PACKAGE__->meta->make_immutable;
1;
