import click
from pkg_resources import get_distribution

from modular_api_cli.modular_cli_group.user import user, user_handler_instance
from modular_api_cli.modular_cli_group.group import group
from modular_api_cli.modular_cli_group.policy import policy
from modular_api_cli.modular_handler.audit_handler import AuditHandler
from modular_api.services import SERVICE_PROVIDER
from modular_api.services.install_service import install_module, uninstall_module, \
    check_and_describe_modules
from modular_api.helpers.decorators import BaseCommand, ResponseDecorator
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger('modular_api')


def audit_handler_instance():
    audit_service = SERVICE_PROVIDER.audit_service()
    return AuditHandler(audit_service=audit_service)


@click.group()
@click.version_option(get_distribution('modular').version, '-v', '--version')
def modular():
    """
    Configuration settings for modular-api
    """
    pass


@modular.command(cls=BaseCommand)
@click.option('--module_path', '-path', type=str,
              required=True,
              help='Path to needed tool source files')
@ResponseDecorator(click.echo, 'Can not install module')
def install(module_path):
    """
    Install module
    """
    return install_module(module_path)


@modular.command(cls=BaseCommand)
@click.option('--module_name', '-name', type=str,
              required=True,
              help='Name of the module to be uninstalled')
@ResponseDecorator(click.echo, 'Can not uninstall module')
def uninstall(module_name):
    """
    Uninstall module
    """
    return uninstall_module(module_name)


@modular.command(cls=BaseCommand)
@click.pass_context
@ResponseDecorator(click.echo, 'Can not describe module')
def describe(ctx):
    """
    Describe all available modules versions and Modular-SDK/CLI version
    """
    table_response = ctx.params.get('table', False)
    return check_and_describe_modules(table_response)


@modular.command(cls=BaseCommand, name='audit')
@click.option('--group', '-g', type=str,
              help='Filter by group name. If "--group" and '
                   '"--from_date" and "--to_date"'
                   'parameters not specified - will be shown '
                   'all events for the last 7 days')
@click.option('--command', '-c', type=str,
              help='Filter by command name')
@click.option('--from_date', '-fd', type=str,
              help='Filter by date from which records are displayed. '
                   'Format yyyy-mm-dd')
@click.option('--to_date', '-td', type=str,
              help='Filter by date until which records are displayed. '
                   'Format yyyy-mm-dd')
@click.option('--limit', '-l', type=click.IntRange(min=1, max=100),
              default=10,
              help='Number of records that will be shown. Default value is 10.'
                   'Will have no effect if "--group" not specified')
@click.option('--invalid', '-I', is_flag=True,
              help='Flag to show only invalid audit events.')
@ResponseDecorator(click.echo, 'Can not describe audit')
def audit(group, command, from_date, to_date, limit, invalid):
    """
    Describes audit
    """
    return audit_handler_instance().describe_audit_handler(
        group=group, command=command, from_date=from_date, to_date=to_date,
        limit=limit, invalid=invalid)


@modular.command(cls=BaseCommand, name='policy_simulator')
@click.option('--user', '-u', type=str,
              help='User which permissions will be checked')
@click.option('--group', '-g', type=str,
              help='Group which permissions will be checked')
@click.option('--policy', '-p', type=str,
              help='Policy which permissions will be checked')
@click.option('--command', '-cmd', type=str,
              required=True,
              help='* Command call string to be checked')
@ResponseDecorator(click.echo, 'Can not describe audit')
def policy_simulator(user, group, policy, command):
    """
    Policy simulator

    Usage:

    1. Get action status by user and command
    modular policy_simulator --user $user_name --command "admin aws add_image"

    2. Get action status by group and command
    modular policy_simulator --group $group_name --command "admin aws add_image"

    3. Get action status by policy and command
    modular policy_simulator --policy $policy_name --command "admin aws add_image"

    """
    params_quantity = sum([bool(param) for param in [user, group, policy]])

    if params_quantity > 1:
        raise ModularApiBadRequestException(
            'Only one of the following parameters: user, group or policy is '
            'allowed for permissions checking'
        )

    return user_handler_instance().policy_simulator_handler(
        user_name=user,
        user_group=group,
        policy_name=policy,
        requested_command=command)


modular.add_command(install)
modular.add_command(user)
modular.add_command(policy)
modular.add_command(group)
