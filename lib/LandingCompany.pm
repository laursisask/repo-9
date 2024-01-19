package LandingCompany;
# ABSTRACT: Manage landing companies for binary.com

=head1 NAME

LandingCompany - A landing company specific configuration.

=head1 SYNOPSIS

    use feature qw(say);
    my $iom = LandingCompany->new(
        short   => 'iom',
        name    => 'Deriv (MX) Ltd',
        address => ["Millennium House", "Victoria Road", "Douglas", "Island"],
        country => 'Isle of Man',
    );
    say "short name is: ", $iom->short;

=head1 DESCRIPTION

This class represents landing companies objects.

=head1 ATTRIBUTES

=cut

use Moose;
use MooseX::StrictConstructor;
use namespace::autoclean;
use LandingCompany::Offerings;
use List::Util qw(any uniq);
use Carp       qw();

=head2 DEFAULT_APP_OFFERINGS

Default app offerings is the application that offers full list of offerings.

=cut

use constant DEFAULT_APP_OFFERINGS => 'default';

use URI;

our $VERSION = '0.33';

=head2 is_disabled

Flag to disable a particular landing company.

=cut

has is_disabled => (
    is      => 'ro',
    default => 0,
);

=head2 broker_codes

A list of broker_codes allowed on a particular landing company

=cut

has broker_codes => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 transaction_checks

List of checks needed to be carried out for transactions (for clients who are buying contracts)

=cut

has transaction_checks => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 client_validation_misc

List of checks needed to be carried out for:

- Clients who are buying on behalf of other clients

=cut

has client_validation_misc => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 short

Short name for the landing company

=cut

has short => (
    is       => 'ro',
    required => 1,
);

=head2 is_virtual

whether the landing company operates on virtual money or not.

=cut

has is_virtual => (
    is      => 'ro',
    default => 0,
);

=head2 is_for_affiliates

whether the landing company is for affiliate accounts.

=cut

has is_for_affiliates => (
    is      => 'ro',
    default => 0,
);

=head2 is_eu

whether the landing company belong to eu region.

=cut

has is_eu => (
    is => 'ro',
);

=head2 name

Full name of the landing company

=cut

has name => (
    is       => 'ro',
    required => 1,
);

=head2 address

Address of the landing company. Should be arrayref to the list of strings forming the address. Optional.

=cut

has address => (
    is => 'ro',
);

=head2 country

Country in which landing company registered

=cut

has country => (
    is       => 'ro',
    required => 1,
);

=head2 legal_allowed_currencies

A hash of currencies which can legally be traded by this company.

In form of {currency1 => type, currency2 => type2}

=cut

has legal_allowed_currencies => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} },
);

=head2 requirements

A hashref of requirements for this company

=cut

has requirements => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} });

=head2 legal_default_currency

The default currency, if any, for this company

=cut

has legal_default_currency => (
    is => 'ro',
);

=head2 residences_default_currency

The default residences currency, if any, for this company

=cut

has residences_default_currency => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} },
);

=head2 legal_allowed_offerings

legal allowed offerings by:

market1:
 - contract_category1
 - contract_category2
market2:
 - contract_category1
 - contract_category2

=cut

has legal_allowed_offerings => (
    is      => 'ro',
    default => sub { {} });

=head2 legal_allowed_contract_categories

A list of contract categories allowed on a particular landing company

=cut

has legal_allowed_contract_categories => (
    is         => 'ro',
    isa        => 'ArrayRef[Str]',
    lazy_build => 1,
);

sub _build_legal_allowed_contract_categories {
    my $self = shift;

    return [sort (uniq(map { @$_ } values %{$self->legal_allowed_offerings}))];
}

=head2 allows_payment_agents

True if clients allowed to use payment agents

=cut

has allows_payment_agents => (
    is      => 'ro',
    default => 0,
);

=head2 ip_check_required

True if clients need IP check

=cut

has ip_check_required => (
    is      => 'ro',
    default => 0,
);

=head2 check_max_turnover_limit_is_set

True if clients need to check that max_turnover_limit is set

=cut

has check_max_turnover_limit_is_set => (
    is      => 'ro',
    default => 0,
);

=head2 changeable_fields
 A hashref of fields this company can allow changes on.
=cut

has changeable_fields => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} });

=head2 ip_mt5_group_check

True if the mt5 group is needed to be checked

=cut

has ip_mt5_group_check => (
    is      => 'ro',
    default => 0,
);

=head2 payment_agents_residence_disable

Country of residence disabled for payment agents

=cut

has payment_agents_residence_disable => (
    is      => 'ro',
    default => '',
);

=head2 has_reality_check

True if reality check is allowed

=cut

has has_reality_check => (
    is      => 'ro',
    default => 0,
);

=head2 tnc_required

True if clients must accept terms & conditions to trade and access cashier

=cut

has tnc_required => (
    is      => 'ro',
    default => 0,
);

=head2 allowed_for_brands

List of brands where landing company is allowed

=cut

has allowed_for_brands => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

has offerings => (
    is         => 'ro',
    lazy_build => 1,
);

sub _build_offerings {
    my $self = shift;
    die 'offerings not defined for landing company[' . $self->short . ']';
}

=head2 marketing_email_consent

Section to hold email consent properties

=cut

has marketing_email_consent => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} },
);

=head2 social_responsibility_check

Required for clients that requires automatic monitoring for social responsibility
Manual for clients where Social responsibility is set manual in backoffice

=cut

has social_responsibility_check => (
    is => 'ro',
);

=head2 qualifying_payment_check_required

True for Landing Companies that require monitoring for the qualifying transaction regulation,
which states that (once the threshold is breached)
authentication is required, when clients reach EUR3K in either deposits/withdrawals within a 30 day period.

=cut

has qualifying_payment_check_required => (
    is => 'ro',
);

=head2 actions

List of events and actions to be performed on the client on that event

=cut

has actions => (
    is      => 'ro',
    isa     => 'HashRef',
    default => sub { {} },
);

=head2 support_professional_client

A boolean value representing whether landing company supports the concept
of professional clients

=cut

has support_professional_client => (
    is      => 'ro',
    default => 0,
);

=head2 is_authentication_mandatory

A boolean value representing whether authentication is mandatory or not

=cut

has is_authentication_mandatory => (
    is      => 'ro',
    default => 0,
);


=head2 first_deposit_auth_check_required

A boolean value representing whether authentication check is required for first deposit or not

=cut

has first_deposit_auth_check_required => (
    is       => 'ro',
    required => 1,
);

=head2 poi_expiration_check_required

A boolean value representing whether POI documents expiration should be checked for clients or not

=cut

has poi_expiration_check_required => (
    is      => 'ro',
    default => 1,
);

=head2 poa_outdated_check_required

A boolean value representing whether POA documents expiration should be checked for clients or not

=cut

has poa_outdated_check_required => (
    is      => 'ro',
    default => 1,
);

has deposit_limit_enabled => (
    is      => 'ro',
    default => 0,
);

=head2 requires_face_similarity_check

A boolean value representing whether face similarity check is active or not

=cut

has requires_face_similarity_check => (
    is      => 'ro',
    default => 0,
);

=head2 unlimited_balance

A boolean flag indicating whether its allowed to have unlimited balance or not.

=cut

has unlimited_balance => (
    is      => 'ro',
    default => 0,
);

=head2 risk_settings

An array containing the list of risk settings applicable in the landing company.
This array can contain any of these values: 
B<aml_thresholds>, B<aml_jurisdiction>, B<mt5_thresholds> and B<mt5_jurisdiction>.

=over 4

=item C<aml_thresholds> indicating that risk thresholds are applicable on Deriv accounts

=item C<aml_jurisdiction> indicating that jurisdiction risk ratings are applicable on Deriv accounts

=item C<mt5_thresholds> indicating that risk thresholds are applicable on MT5 accounts

=item C<mt5_jurisdiction> indicating that jurisdiction risk ratings are applicable on MT5 accounts

=back

=cut

has risk_settings => (
    is      => 'ro',
    default => sub { [] },
);

=head2 risk_lookup

The same data in B<risk_settings> reporesented as a hash for easier lookup.

=cut

sub risk_lookup {
    my $self = shift;

    return {map { $_ => 1 } $self->risk_settings->@*};
}

=head2 payout_freezing_funds

A boolean value representing whether client's funds should be debited upon payout create or not

=cut

has payout_freezing_funds => (
    is      => 'ro',
    default => 0
);

=head2 default_product_type

Default product type for the landing company. multi_barrier is no longer supported.
The attribute can have one of the next values: 'basic', undef.

=cut

has default_product_type => (
    is      => 'ro',
    lazy    => 1,
    builder => '_build_default_product_type',
);

sub _build_default_product_type {
    my $self = shift;

    return 'basic' if $self->offerings->{basic}{default} ne 'none';

    return undef;
}

=head2 allowed_landing_companies_for_authentication_sync

List of landing companies allowed for authentication sync

=cut

has allowed_landing_companies_for_authentication_sync => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 allowed_landing_companies_for_age_verification_sync

List of landing companies allowed for age verification sync

=cut

has allowed_landing_companies_for_age_verification_sync => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 allowed_poi_providers

List of allowed POI providers

=cut

has allowed_poi_providers => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 mt5_require_deriv_account_at

List of landing companies which client need to create deriv account there before MT5 account creation will be available 

=cut

has mt5_require_deriv_account_at => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

=head2 p2p_available

A boolean value representing whether the P2P cashier is available or not.

=cut

has p2p_available => (
    is      => 'ro',
    default => 0,
);

=head2 lifetime_withdrawal_limit_check

A boolean value representing whether the lifetime withdrawal limit check is required or not.

=cut

has lifetime_withdrawal_limit_check => (
    is      => 'ro',
    default => 0,
);

=head2 skip_authentication

A boolean value representing whether KYC checks can be skipped..

=cut

has skip_authentication => (
    is      => 'ro',
    default => 0,
);

=head2 mt5_transfer_with_different_currency_allowed

A boolean value representing whether the mt5 transfer with different currency is allowed or not.

=cut

has mt5_transfer_with_different_currency_allowed => (
    is      => 'ro',
    default => 1,
);

=head2 is_currency_legal

Returns true of the given currency is legal allowed

=cut

sub is_currency_legal {
    my ($self, $currency) = @_;

    return exists $self->legal_allowed_currencies->{$currency};
}

=head2 basic_offerings

Returns a LandingCompany::Offerings object representing the basic offerings for a specific landing company

=cut

sub basic_offerings {
    my ($self, $config, $app_offerings) = @_;

    $app_offerings //= DEFAULT_APP_OFFERINGS;
    $config->{legal_allowed_offerings} = $self->legal_allowed_offerings;

    return LandingCompany::Offerings->get({
        name     => $self->short,
        filename => $self->offerings->{basic}{default},
        app      => $app_offerings,
        config   => $config
    });
}

=head2 basic_offerings_for_country

Returns LandingCompany::Offerings object for a specific country.

=cut

sub basic_offerings_for_country {
    my ($self, $country_code, $config, $app_offerings) = @_;

    $app_offerings //= DEFAULT_APP_OFFERINGS;
    $config->{legal_allowed_offerings} = $self->legal_allowed_offerings;

    if (my $override = $self->offerings->{basic}{override}{$country_code}) {
        return LandingCompany::Offerings->get({
            name     => $self->short . '_' . $country_code,
            filename => $override,
            app      => $app_offerings,
            config   => $config
        });
    }

    return $self->basic_offerings($config, $app_offerings);
}

=head2 is_email_consent_required

Flag to indicate if email consent is required for landing company

=cut

sub is_email_consent_required {
    my $self = shift;

    return $self->marketing_email_consent->{required};
}

=head2 get_email_consent_default

Get default value for email consent, either 0 or 1, for landing company

=cut

sub get_email_consent_default {
    my $self = shift;

    return $self->marketing_email_consent->{default};
}

=head2 virtual_account_default_balance

default balance for virtual account

=cut

has virtual_account_default_balance => (
    is      => 'ro',
    default => 0,
);

=head2 set_self_exclusion_notify

A boolean value representing whether an email should be sent to payments team
when client sets self exlusion limits

=cut

has self_exclusion_notify => (
    is      => 'ro',
    default => 0
);

=head2 available_mt5_currency_group

MT5 accounts are bucketed into groups with different denominated currency.
This lists the available currencies for a landing company.

Defaults to empty array reference.

=cut

has available_mt5_currency_group => (
    is      => 'ro',
    default => sub { [] },
);

=head2 available_trading_platform_currency_group

Trading platforms accounts are bucketed into groups with different denominated currency.
This hash includes a list for each trading platform available, as for now `dxtrade`.

Defaults to empty hash reference.

=cut

has available_trading_platform_currency_group => (
    is      => 'ro',
    default => sub { {} },
);

=head2 get_default_currency

Gets the default currency.

It takes the following params:

=over 4

=item C<residence> The 2 letters country code.

=back

Returns,
    the currency code for the specified residence if defined,
    otherwise fallbacks to the landing company default curency.

=cut

sub get_default_currency {
    my ($self, $residence) = @_;
    return $self->legal_default_currency unless $residence;
    return $self->residences_default_currency->{$residence} // $self->legal_default_currency;
}

=head2 legal_allowed_markets

A list of markets which are allowed on particular landing company.
By default it returns the legal allowed markets on particular landing company.
Otherwise, if a C<$country> is given, returns the markets for the specified country

=over 4

=item * C<self> A LandingCompany::Registry object.

=item * C<$country> The client's residence country. If none is given it will fallback to default

=back

=cut

sub legal_allowed_markets {
    my $self    = shift;
    my $config  = shift;
    my $country = shift // 'default';

    return [sort keys %{$self->legal_allowed_offerings}] if $country eq "default";

    # If a country is given, then return the markets for this country
    my $offerings = $self->basic_offerings_for_country($country, $config);

    return [$offerings->values_for_key('market')];

}

=head2 is_suspended

A boolean value representing whether this landing company is suspended

=cut

has is_suspended => (
    is      => 'ro',
    default => 0,
);

=head2 aliases

A list of short codes that can be used to reference this L<LandingCompany>

=cut

has aliases => (
    is         => 'ro',
    isa        => 'ArrayRef[Str]',
    lazy_build => 1,
);

=head2 idv_auth_methods

List of allowed IDV authentication methods per landing company:
- idv_address: this is when IDV verification additionally provides an address along with the verification report (no POA check required). 
- idv_photo: this is when IDV verification additionally provides a picture along with the verification report (no POA check required). 
- idv_address_and_photo: this is when IDV verification additionally provides an address and a picture along with the verification report (no POA check required). 
- idv_poa:  this is when IDV verification is submitted along a valid POA. 

=cut

has idv_auth_methods => (
    is      => 'ro',
    isa     => 'ArrayRef[Str]',
    default => sub { [] },
);

__PACKAGE__->meta->make_immutable;

1;
