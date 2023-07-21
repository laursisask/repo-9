import click

from modular_api.services import SERVICE_PROVIDER
from modular_api_cli.modular_handler.user_handler import UserHandler
from modular_api.helpers.decorators import BaseCommand, ResponseDecorator, produce_audit


@click.group()
def user():
    """
    Manages users that can submit request to server
    """


def user_handler_instance():
    user_service = SERVICE_PROVIDER.user_service()
    group_service = SERVICE_PROVIDER.group_service()
    policy_service = SERVICE_PROVIDER.policy_service()
    return UserHandler(user_service=user_service,
                       group_service=group_service,
                       policy_service=policy_service)


@user.command(cls=BaseCommand)
@click.option('--username', '-u', type=str, required=True,
              help='Username that will be added to trusted users')
@click.option('--group', '-g', type=str, required=True, multiple=True,
              help='Group name(s) that will be attached to user')
@click.option('--password', '-p', type=str, required=False,
              help='Password that will be attached to user. In case password '
                   'is not provided, it will be generated automatically.')
@ResponseDecorator(click.echo, 'Can not add user')
@produce_audit(secured_params=['password'])
def add(username, group, password):
    """
    Add user to white list
    """
    return user_handler_instance().add_user_handler(
        username=username, groups=group, password=password)


@user.command(cls=BaseCommand)
@click.option('--username', '-u', type=str,
              required=True,
              help='Username that will be deleted from white list')
@ResponseDecorator(click.echo, 'Can not delete user')
@produce_audit()
def delete(username):
    """
    Deletes user from white list
    """
    return user_handler_instance().delete_user_handler(username=username)


@user.command(cls=BaseCommand)
@click.option('--username', '-u', type=str, help='Username', required=True)
@click.option('--reason', '-rsn', required=True,
              help='The textual reason of user blocking')
@ResponseDecorator(click.echo, 'Can not block user')
@produce_audit()
def block(username, reason):
    """
    Sets user`s state to "blocked"
    """
    return user_handler_instance().block_user_handler(username=username,
                                                      reason=reason)


@user.command(cls=BaseCommand)
@click.option('--username', '-u', type=str, help='Username', required=True)
@click.option('--reason', '-rsn', required=True,
              help='The textual reason of user unblocking')
@ResponseDecorator(click.echo, 'Can not block user')
@produce_audit()
def unblock(username, reason):
    """
    Resets user`s state from blocked
    """
    return user_handler_instance().unblock_user_handler(username=username,
                                                        reason=reason)


@user.command(cls=BaseCommand, name='change_password')
@click.option('--username', '-u', type=str, help='Username', required=True)
@click.option('--password', '-pwd', type=str, help='New user password',
              required=True)
@ResponseDecorator(click.echo, 'Can not change user password')
@produce_audit(secured_params=['password'])
def change_password(username, password):
    """
    Changes user`s password
    """
    return user_handler_instance().change_user_password_handler(
        username=username,
        password=password
    )


@user.command(cls=BaseCommand, name='add_to_group')
@click.option('--username', '-u', type=str, help='Username', required=True)
@click.option('--group', '-g', type=str, multiple=True,
              help='Group name(s) that will be attached to user')
@ResponseDecorator(click.echo, 'Can not update user')
@produce_audit()
def add_to_group(username, group):
    """
    Adds group(s) to the user
    """
    return user_handler_instance().manage_user_groups_handler(
        username=username, groups=group, action='add'
    )


@user.command(cls=BaseCommand, name='remove_from_group')
@click.option('--username', '-u', type=str, help='Username', required=True)
@click.option('--group', '-g', type=str, multiple=True,
              help='Group name(s) that will be detached from user')
@ResponseDecorator(click.echo, 'Can not update user')
@produce_audit()
def remove_from_group(username, group):
    """
    Removes group(s) from the user
    """
    return user_handler_instance().manage_user_groups_handler(
        username=username, groups=group, action='remove'
    )


@user.command(cls=BaseCommand)
@click.option('--username', '-u', type=str,
              help='Username. If not specified - all existing users will '
                   'be listed')
@ResponseDecorator(click.echo, 'Can not describe user')
def describe(username):
    """
    Describes user(s) information
    """
    return user_handler_instance().describe_user_handler(username=username)


@user.command(cls=BaseCommand, name='set_meta_attribute')
@click.option('--username', '-u', type=str, required=True,
              help='User name')
@click.option('--key', '-k', type=str, required=True,
              help='Parameter name')
@click.option('--value', '-v', type=str, required=True,
              multiple=True,
              help='Parameter value. Multiple values allowed (e.g. '
                   '--value value1 --value value2).')
@ResponseDecorator(click.echo, 'Can not set user meta')
def set_meta_attribute(username, key, value):
    """
    Add or replace if exists user meta information with parameter name and its
    values that are allowed to be executed by the user
    """
    return user_handler_instance().set_user_meta_handler(
        username=username, key=key, values=value)


@user.command(cls=BaseCommand, name='update_meta_attribute')
@click.option('--username', '-u', type=str, required=True,
              help='User name')
@click.option('--key', '-k', type=str, required=True,
              help='Parameter name')
@click.option('--value', '-v', type=str, required=True,
              multiple=True,
              help='Parameter value. Multiple values allowed (e.g. '
                   '--value value1 --value value2).')
@ResponseDecorator(click.echo, 'Can not update user meta')
def update_meta_attribute(username, key, value):
    """
    Update user meta information with parameter name and its values that are
    allowed to be executed by the user
    """
    return user_handler_instance().update_user_meta_handler(
        username=username, key=key, values=value)


@user.command(cls=BaseCommand, name='delete_meta_attribute')
@click.option('--username', '-u', type=str, required=True,
              help='User name')
@click.option('--key', '-k', type=str, required=True,
              multiple=True,
              help='Parameter name. Multiple values allowed (e.g. '
                   '--key value1 --key value2).')
@ResponseDecorator(click.echo, 'Can not delete user meta')
def delete_meta_attribute(username, key):
    """
    Delete parameter/s name from the user meta information
    """
    return user_handler_instance().delete_user_meta_handler(
        username=username, keys=key)


@user.command(cls=BaseCommand, name='reset_meta')
@click.option('--username', '-u', type=str, required=True,
              help='User name')
@ResponseDecorator(click.echo, 'Can not reset user meta')
def reset_meta(username):
    """
    Erase all meta information from the user item
    """
    return user_handler_instance().reset_user_meta_handler(
        username=username)


@user.command(cls=BaseCommand, name='get_meta')
@click.option('--username', '-u', type=str, required=True,
              help='User name')
@ResponseDecorator(click.echo, 'Can not describe user meta')
def get_meta(username):
    """
    Describe meta information for the specified user
    """
    return user_handler_instance().describe_user_meta_handler(
        username=username)
