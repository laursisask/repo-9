import copy
from hashlib import sha256

from modular_api.helpers.exceptions import ModularApiConfigurationException
from modular_api.helpers.log_helper import get_logger

ALLOW = 'Allow'
DENY = 'Deny'

_LOG = get_logger(__name__)


def policy_sort(policy_list: list) -> dict:
    """
    Sort all user policies by "Effect" - Allow/Deny.
    """
    deny_actions = dict()
    allow_actions = dict()
    # todo check for old-style policies, remove after 3.85 prod update
    for item in policy_list:
        if item.get('Group') or item.get('MountPoint'):
            _LOG.error(f'Found old style RBAC v1 policy. Some policy still '
                       f'contains "MountPoint":"{item.get("MountPoint")}" and/or'
                       f' "Group":"{item.get("Group")}"')
            raise ModularApiConfigurationException(
                f'Invalid policies detected. Please contact support team'
            )
    # =====
    for item in policy_list:
        module = item['Module']
        allow = True if item['Effect'] == ALLOW else False
        resources = item['Resources']
        if allow:
            if module not in allow_actions.keys():
                allow_actions[module] = []
            allow_actions[module].extend(resources)
        else:
            if module not in deny_actions.keys():
                deny_actions[module] = []
            deny_actions[module].extend(resources)

    policy = {ALLOW: set(), DENY: set()}
    for module, items in allow_actions.items():
        for value in items:
            policy[ALLOW].add(f'/{module}@{value}')
    for module, items in deny_actions.items():
        for value in items:
            policy[DENY].add(f'/{module}@{value}')

    return policy


def check_entire_module(*args) -> bool:
    """
    Check if entire module allowed
    """
    allowed = args[0]
    module = args[1]
    for val in allowed:
        if val == f'{module}*':
            return True
    return False


def check_module_present(*args) -> bool:
    """
    Check if module name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    for val in allowed:
        if val.startswith(module):
            return True
    return False


def check_entire_group(*args) -> bool:
    """
    Check if entire group allowed
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    for val in allowed:
        if val == f'{module}{group}:*':
            return True
    return False


def check_in_group(*args) -> bool:
    """
    Check if group name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    for val in allowed:
        if val.startswith(f'{module}{group}'):
            return True
    return False


def check_entire_subgroup(*args) -> bool:
    """
    Check if entire subgroup allowed
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val == f'{module}{group}/{subgroup}:*':
            return True
    return False


def check_in_subgroup(*args) -> bool:
    """
    Check if subgroup name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val.startswith(f'{module}{group}/{subgroup}'):
            return True
    return False


def check_root_command(*args) -> bool:
    """
    Check if root command name is in allowed module
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    for val in allowed:
        if val == f'{module}{command}':
            return True
    return False


def check_group_command(*args) -> bool:
    """
    Check if command name is in allowed group
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    group = args[3]
    for val in allowed:
        if val == f'{module}{group}:{command}':
            return True
    return False


def check_subgroup_command(*args) -> bool:
    """
    Check if command name is in allowed subgroup
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val == f'{module}{group}/{subgroup}:{command}':
            return True
    return False


def check_permission(policy: list, module: str, command=None, group=None,
                     subgroup=None, atype: str = 'default') -> bool:
    """
    1. Check user permissions by "Deny" rules
    2. Check user permissions by "Allow" rules
    """
    policy = policy_sort(policy)
    module = f'{module}@'
    denied = policy[DENY]
    allowed = policy[ALLOW]
    # ===== check DENIED =====
    for value in denied:
        if value.startswith('/*@'):
            return False
    if f'{module}*' in denied:
        return False
    if f'{module}{command}' in denied:
        return False
    if f'{module}{group}:*' in denied:
        return False
    if f'{module}{group}:{command}' in denied:
        return False
    if f'{module}{group}/{subgroup}:*' in denied:
        return False
    if f'{module}{group}/{subgroup}:{command}' in denied:
        return False
    # ====== check ALLOWED =====
    for value in allowed:
        if value.startswith('/*@'):
            return True
    allow_map = {
        "entire_module": check_entire_module,
        "module": check_module_present,
        "entire_group": check_entire_group,
        "group": check_in_group,
        "entire_subgroup": check_entire_subgroup,
        "subgroup": check_in_subgroup,
        "root_command": check_root_command,
        "group_command": check_group_command,
        "subgroup_command": check_subgroup_command
    }
    verifier = allow_map.get(atype)
    if verifier:
        return verifier(allowed, module, command, group, subgroup)

    return True


def filter_meta_by_deny_priority(policy: list, all_meta: dict) -> dict:
    """
    Check user permissions by "Deny" rules:
    1. Check if module allowed
    2. Check if command in module allowed
    3. Check if group allowed
    4. Check if command in group allowed
    5. Check if subgroup allowed
    6. Check if command in subgroup allowed
    """
    bd = 'body'
    user_commands = copy.deepcopy(all_meta)
    for module, module_content in all_meta.items():

        allow_module = check_permission(policy=policy, module=module)
        if not allow_module:
            del user_commands[module]
            continue

        for item, item_content in module_content[bd].items():
            if item_content.get('type') == 'group':
                group = item
                allow_group = check_permission(
                    policy=policy, module=module, group=group)
                if not allow_group:
                    del user_commands[module][bd][group]
                    continue

                for group_item, group_content in item_content[bd].items():
                    if group_content.get('type') == 'group':
                        subgroup = group_item
                        allow_subgroup = check_permission(
                            policy=policy, module=module,
                            group=group, subgroup=subgroup)
                        if not allow_subgroup:
                            del user_commands[module][bd][group][bd][subgroup]
                            continue

                        for subgroup_item, subgroup_content in group_content[
                            bd].items():
                            subgroup = group_item
                            cmd = subgroup_item
                            allow_sub_command = check_permission(
                                policy=policy, module=module,
                                group=group, subgroup=subgroup, command=cmd)
                            if not allow_sub_command:
                                del user_commands[module][bd][group][bd][subgroup][bd][cmd]
                                continue

                    else:
                        cmd = group_item
                        allow_group_command = check_permission(
                            policy=policy, module=module, group=group,
                            command=cmd)
                        if not allow_group_command:
                            del user_commands[module][bd][group][bd][cmd]

            else:
                cmd = item
                allow_module_command = check_permission(
                    policy=policy, module=module, command=cmd)
                if not allow_module_command:
                    del user_commands[module][bd][cmd]

    return user_commands


def filter_meta_by_allow_priority(policy: list, all_meta: dict) -> dict:
    """
    Check user permissions by "Allow" rules:
    1. Check if module allowed
    2. Check if command in module allowed
    3. Check if group allowed
    4. Check if command in group allowed
    5. Check if subgroup allowed
    6. Check if command in subgroup allowed
    """
    bd = 'body'
    user_commands = copy.deepcopy(all_meta)

    for module, module_content in all_meta.items():

        allow_entire_module = check_permission(policy=policy, module=module,
                                               atype='entire_module')
        if allow_entire_module:
            continue

        allow_in_module = check_permission(policy=policy, module=module,
                                           atype='module')
        if not allow_in_module:
            del user_commands[module]
            continue

        for item, item_content in module_content[bd].items():
            if item_content.get('type') == 'group':
                group = item
                allow_entire_group = check_permission(
                    policy=policy, module=module, group=group, atype='entire_group')
                if allow_entire_group:
                    continue
                allow_in_group = check_permission(
                    policy=policy, module=module, group=group, atype='group')
                if not allow_in_group:
                    del user_commands[module][bd][group]
                    continue

                for group_item, group_content in item_content[bd].items():
                    if group_content.get('type') == 'group':
                        subgroup = group_item
                        allow_entire_subgroup = check_permission(
                            policy=policy, module=module,
                            group=group, subgroup=subgroup, atype='entire_subgroup')
                        if allow_entire_subgroup:
                            continue
                        allow_in_subgroup = check_permission(
                            policy=policy, module=module,
                            group=group, subgroup=subgroup, atype='subgroup')
                        if not allow_in_subgroup:
                            del user_commands[module][bd][group][bd][subgroup]
                            continue

                        for subgroup_item, subgroup_content in group_content[
                            bd].items():
                            subgroup = group_item
                            cmd = subgroup_item
                            allow_sub_command = check_permission(
                                policy=policy, module=module,
                                group=group, subgroup=subgroup, command=cmd,
                                atype='subgroup_command')
                            if not allow_sub_command:
                                del user_commands[module][bd][group][bd][subgroup][bd][cmd]
                                continue
                    else:
                        cmd = group_item
                        allow_group_command = check_permission(
                            policy=policy, module=module, group=group,
                            command=cmd, atype='group_command')
                        if not allow_group_command:
                            del user_commands[module][bd][group][bd][cmd]
            else:
                cmd = item
                allow_module_command = check_permission(
                    policy=policy, module=module, command=cmd,
                    atype='root_command')
                if not allow_module_command:
                    del user_commands[module][bd][cmd]

    return user_commands


# todo refactor mount point to be set by module
def filter_commands_by_permissions(
        available_commands: dict, group_policy: list) -> dict:
    """
    Filter for user permissions. The rules summary described below:
    1) Deny effect has more priority than Allow;
    2) If some command/groups/subgroups/modules are not in user policy(ies)
       then they will not be available to use;
    3) Entire API rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "*",
            "Resources": [
                "*"
            ]
        }
    4) Module rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "*"
            ]
        }
    5) Module-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$command_name_1",
                "$command_name_2",
                ...
                "$command_name_N",
            ]
        }
    6) Module-group rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$group_name_1:*",
                "$group_name_2:*",
                ...
                "$group_name_N:*",
            ]
        }
    7) Module-group-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$group_name_1:$command_name_1",
                "$group_name_2:$command_name_2",
                ...
                "$group_name_N:$command_name_N",
            ]
        }
    8) Module-group-subgroup rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "group_name_1/$subgroup_name_1:*",
                "group_name_2/$subgroup_name_2:*",
                ...
                "group_name_N/$subgroup_name_N:*",
            ]
        }
    9) Module-group-subgroup-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "group_name_1/$subgroup_name_1:$command_name_1",
                "group_name_2/$subgroup_name_2:$command_name_2",
                ...
                "group_name_N/$subgroup_name_N:$command_name_N",
            ]
        }
    """
    all_meta = copy.deepcopy(available_commands)
    if '/' in available_commands.keys():
        #  "/" stands for "m3admin" endpoint in API-meta, but in policy
        #  we use "m3admin" in module name property instead of "/"
        all_meta['/m3admin'] = all_meta['/']
        del all_meta['/']
    del available_commands

    filtered_by_deny = filter_meta_by_deny_priority(
        policy=group_policy, all_meta=all_meta)
    del all_meta
    filtered_by_allow = filter_meta_by_allow_priority(
        policy=group_policy, all_meta=filtered_by_deny)

    user_meta = dict()
    for key, value in filtered_by_allow.items():
        #  rollback from temp "m3admin" module name to default endpoint "/"
        if key == '/m3admin':
            user_meta['/'] = value
        else:
            user_meta[key] = value

    return user_meta


def hash_user_name(user_name):
    return sha256(user_name.encode('utf-8')).hexdigest()

