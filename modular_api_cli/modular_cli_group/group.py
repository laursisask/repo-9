import click

from modular_api_cli.modular_handler.group_handler import GroupHandler
from modular_api.services import SERVICE_PROVIDER
from modular_api.helpers.decorators import BaseCommand, ResponseDecorator, \
    produce_audit


@click.group()
def group():
    """
    Manages groups which using to define user permissions
    """


def group_handler_instance():
    return GroupHandler(
        group_service=SERVICE_PROVIDER.group_service,
        policy_service=SERVICE_PROVIDER.policy_service,
        user_service=SERVICE_PROVIDER.user_service
    )


@group.command(cls=BaseCommand)
@click.option('--group', '-g', type=str, required=True,
              help='Group name')
@click.option('--policy', '-p', type=str, required=True, multiple=True,
              help='Policy name that will be attached to the group')
@ResponseDecorator(click.echo, 'Can not add group')
@produce_audit()
def add(group, policy):
    """
    Adds group with allowed actions based on provided policy(ies) name(s)
    """
    return group_handler_instance().add_group_handler(
        group=group, policies=policy)


@group.command(cls=BaseCommand, name='add_policy')
@click.option('--group', '-g', type=str, required=True,
              help='Group name')
@click.option('--policy', '-p', type=str, required=True, multiple=True,
              help='Policy name that will be attached to the group')
@ResponseDecorator(click.echo, 'Can not add policy to the group')
@produce_audit()
def add_policy(group, policy):
    """
    Adds policies to already existing group
    """
    return group_handler_instance().manage_group_policies_handler(
        group=group, policies=policy, action='add')


@group.command(cls=BaseCommand, name='delete_policy')
@click.option('--group', '-g', type=str, required=True,
              help='Group name')
@click.option('--policy', '-p', type=str, required=True, multiple=True,
              help='Policy name that will be detached from the group')
@ResponseDecorator(click.echo, 'Can not delete policy')
@produce_audit()
def delete_policy(group, policy):
    """
    Deletes policies from already existing group
    """
    return group_handler_instance().manage_group_policies_handler(
        group=group, policies=policy, action='remove')


@group.command(cls=BaseCommand)
@click.option('--group', '-g', type=str,
              help='Group name. If not specified then all existing groups will'
                   'be listed')
@ResponseDecorator(click.echo, 'Can not describe group')
def describe(group):
    """
    Describes specified group or list all groups
    """
    return group_handler_instance().describe_group_handler(group=group)


@group.command(cls=BaseCommand)
@click.option('--group', '-g', type=str, required=True,
              help='Group name')
@ResponseDecorator(click.echo, 'Can not delete group')
@produce_audit()
def delete(group):
    """
    Deletes group
    """
    return group_handler_instance().delete_group_handler(group=group)
