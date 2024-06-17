import click

from modular_api_cli.modular_handler.policy_handler import PolicyHandler
from modular_api.services import SERVICE_PROVIDER
from modular_api.helpers.decorators import ResponseDecorator, BaseCommand, produce_audit


@click.group()
def policy():
    """
    Manages policies documents which define groups permissions
    """


def policy_handler_instance():
    return PolicyHandler(
        policy_service=SERVICE_PROVIDER.policy_service,
        group_service=SERVICE_PROVIDER.group_service
    )


@policy.command(cls=BaseCommand)
@click.option('--policy', '-p', type=str, required=True,
              help='Policy name')
@click.option('--policy_path', '-path', type=str, required=True,
              help='Path to policy document. File extension: *.json')
@ResponseDecorator(click.echo, 'Can not add policy')
@produce_audit()
def add(policy, policy_path):
    """
    Creates a policy that defines the permissions you can assign to a group.
    """
    return policy_handler_instance().add_policy_handler(
        policy=policy, policy_path=policy_path)


@policy.command(cls=BaseCommand)
@click.option('--policy', '-p', type=str, required=True,
              help='Policy name')
@click.option('--policy_path', '-path', type=str,
              help='Path to policy document. File extension: *.json')
@ResponseDecorator(click.echo, 'Can not update policy')
@produce_audit()
def update(policy, policy_path):
    """
    Rewrites policy permissions.
    """
    return policy_handler_instance().update_policy_handler(
        policy=policy, policy_path=policy_path)


@policy.command(cls=BaseCommand)
@click.option('--policy', '-p', type=str,
              help='Policy name. All existed policies will be described in '
                   'case if parameter not provided')
@click.option('--expand', '-E', is_flag=True,
              help='Specify to describe policies with content. '
                   'Has no effect and always \'True\' if \'--policy\' '
                   'parameter passed')
@click.option('--json', is_flag=True,
              help='Show response as JSON. Can not be used with --table '
                   'parameter')
@click.pass_context
@ResponseDecorator(click.echo, 'Can not describe policy')
def describe(ctx, policy, expand, json):
    """
    Describes permissions defined in policy.
    """
    if policy:
        expand = True

    table = ctx.params.get('table', False)
    return policy_handler_instance().describe_policy_handler(
        policy=policy, expand_view=expand, json_response=json,
        table_response=table
    )


@policy.command(cls=BaseCommand)
@click.option('--policy', '-p', type=str, required=True,
              help='Permission policy name')
@ResponseDecorator(click.echo, 'Can not delete policy')
@produce_audit()
def delete(policy):
    """
    Deletes policy by provided name
    """
    return policy_handler_instance().delete_policy_handler(policy=policy)
