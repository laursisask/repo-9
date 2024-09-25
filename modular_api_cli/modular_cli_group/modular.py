import multiprocessing

import bottle
import click

from modular_api.helpers.decorators import BaseCommand, ResponseDecorator
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import init_console_handler, get_logger
from modular_api.index import WSGIApplicationBuilder, initialize
from modular_api.services import SERVICE_PROVIDER
from modular_api.services import SP
from modular_api.services.install_service import (
    check_and_describe_modules,
    install_module,
    uninstall_module,
)
from modular_api.version import __version__
from modular_api_cli.modular_cli_group.group import group
from modular_api_cli.modular_cli_group.policy import policy
from modular_api_cli.modular_cli_group.user import user, user_handler_instance
from modular_api_cli.modular_handler.audit_handler import AuditHandler
from modular_api_cli.modular_handler.usage_handler import UsageHandler

_LOG = get_logger(__name__)

DEFAULT_NUMBER_OF_WORKERS = (multiprocessing.cpu_count() * 2) + 1


def audit_handler_instance():
    return AuditHandler(audit_service=SERVICE_PROVIDER.audit_service)


def stats_handler_instance():
    return UsageHandler(usage_service=SERVICE_PROVIDER.usage_service)


@click.group()
@click.version_option(__version__, '-v', '--version')
def modular():
    """
    Configuration settings for modular-api
    """


@modular.command(name='run')
@click.option('--host', '-h', default='0.0.0.0', required=False, type=str,
              help='Host to start the server', show_default=True)
@click.option('--port', '-p', default=8085, type=int, required=False,
              help='Host to start the server', show_default=True)
@click.option('--prefix', '-pr', type=str, required=False, default='',
              help='Global api prefix. By default there is no prefix')
@click.option('--gunicorn', '-g', is_flag=True,
              help='Whether to run the server using gunicorn')
@click.option('--workers', '-nw', required=False, type=int,
              default=DEFAULT_NUMBER_OF_WORKERS, show_default=True,
              help='Number of gunicorn workers. Has effect only if '
                   '--gunicorn flag is set')
@click.option('--worker_timeout', '-wt', default=0, type=int,
              help='Gunicorn worker timeout in seconds. '
                   'By default there is no timeout')
@click.option('--swagger', is_flag=True, help='Whether to server swagger')
@click.option('--swagger_prefix', type=str, default='/swagger',
              help='Swagger path prefix', show_default=True)
def run(host: str, port: int, prefix: str, gunicorn: bool, workers: int,
        worker_timeout: int, swagger: bool, swagger_prefix: str):
    """
    Starts modular server
    """
    init_console_handler()
    initialize()
    application = WSGIApplicationBuilder(
        env=SP.env,
        prefix=prefix,
        swagger=swagger,
        swagger_prefix=swagger_prefix
    ).build()

    if gunicorn:
        from modular_api.web_service.app_gunicorn import \
            ModularAdminGunicornApplication
        options = {
            'bind': f'{host}:{port}',
            'workers': workers,
            'timeout': worker_timeout,
            'max_requests': 50,  # to limit the damage of memory leaks
            'max_requests_jitter': 20
        }
        ModularAdminGunicornApplication(application, options).run()
    else:
        bottle.run(application, host=host, port=port)


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


@modular.command(cls=BaseCommand, name='describe')
@ResponseDecorator(click.echo, 'Can not describe module', custom_view=True)
def describe(json, table):
    """
    Describe all available modules versions and Modular-SDK/CLI version.
    """
    return check_and_describe_modules(table_response=table, json_response=json)


@modular.command(cls=BaseCommand, name='get_stats')
@click.option('--from_month', '-fm', type=str,
              help='Filter by month from which records are displayed. '
                   'Format "yyyy-mm". If not specified - current month will '
                   'be used')
@click.option('--to_month', '-tm', type=str,
              help='Filter by month until which records are displayed. '
                   'Format yyyy-mm. If not specified - next month will be '
                   'used')
@click.option('--display_table', '-D', is_flag=True,
              help='Flag to show report in terminal. If not specified - report '
                   'will be stored into the file')
@click.option('--path', '-p', type=str,
              help='Directory path to saving report file. If not specified - '
                   'report will be saved in user home directory')
@ResponseDecorator(click.echo, 'Can not get statistic')
def get_stats(from_month, to_month, display_table, path):
    """
    Saves usage statistic to a file
    """
    return stats_handler_instance().get_stats_handler(
        from_month=from_month, to_month=to_month, display_table=display_table,
        path=path)


@modular.command(cls=BaseCommand, name='audit')
@click.option('--group', '-g', type=str,
              help='Filter by group name. If "--group" and "--from_date" and '
                   '"--to_date" parameters not specified - will be shown all '
                   'events for the last 7 days')
@click.option('--command', '-c', type=str, help='Filter by command name')
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
        limit=limit, invalid=invalid,
    )


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
