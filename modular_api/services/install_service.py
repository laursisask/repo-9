import json
import os
from pathlib import Path
import subprocess
import shlex
from distutils.dir_util import remove_tree
from shutil import copytree, ignore_patterns
from unittest.mock import MagicMock
import pkg_resources
from packaging import version
from ddtrace import tracer
from version import modular_api_version as api_version
from modular_api.helpers.constants import WINDOWS, LINUX, MODULES_DIR, \
    API_MODULE_FILE, MODULE_NAME_KEY, CLI_PATH_KEY, MOUNT_POINT_KEY, \
    TOOL_VERSION_MAPPING, DEPENDENCIES, MIN_VER
from modular_api.commands_generator import generate_valid_commands
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException, \
    ModularApiConfigurationException
from modular_api.helpers.log_helper import get_logger

DESCRIPTOR_REQUIRED_KEYS = (CLI_PATH_KEY, MOUNT_POINT_KEY, MODULE_NAME_KEY)
MODULAR_ADMIN_ROOT_PATH = os.path.split(os.path.dirname(__file__))[0]
tracer.configure(writer=MagicMock())


def install_module_with_destination_folder(paths_to_module: str):
    """
    Installing module by path
    :param paths_to_module: path to the modules
    :return: stdout, stderror of the installation process
    """
    _LOG = get_logger('install_module_with_destination_folder')
    if not paths_to_module:
        _LOG.info(f"Path not found: {paths_to_module}")
        raise AssertionError(f"Path not found: {paths_to_module}")
    if os.path.isfile(paths_to_module):
        _LOG.info(f"Path not found: {paths_to_module}")
        raise AssertionError(
            f'The path {[paths_to_module]} to the module is file. '
            f'Please specify the path to folder of the module which '
            f'consist of setup.py.')
    _LOG.info(f"Going to execute pip install command for {paths_to_module}")
    os_name = os.name
    if os_name == WINDOWS:
        command = f'pip install -e {paths_to_module}'
        terminal_process = subprocess.Popen(command,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
    elif os_name == LINUX:
        command = f'pip install -e {paths_to_module}'
        terminal_process = subprocess.Popen(shlex.split(command),
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
    else:
        message = f'The {os_name} OS is not supported by tool.'
        raise ModularApiConfigurationException(message)
    stdout, stderr = terminal_process.communicate()
    if stdout is not None:
        stdout = stdout.decode('utf-8')
        _LOG.info(f"Out: {stdout}")
    if stderr is not None:
        stderr = stderr.decode('utf-8')
        _LOG.error(f"Errors: {stderr}")
        _LOG.info('Installation completed with errors')
        raise ModularApiConfigurationException(stderr)
    _LOG.info('Installation completed')


def write_generated_meta_to_file(path_to_file, mount_point, groups_meta):
    if not os.path.isfile(path_to_file):
        cmd_base_content = json.dumps({mount_point: groups_meta}, indent=2)
    else:
        with open(path_to_file, 'r') as cmd_base:
            cmd_base_content = json.load(cmd_base)
        cmd_base_content.update({mount_point: groups_meta})
        cmd_base_content = json.dumps(cmd_base_content, indent=2)

    with open(path_to_file, 'w') as cmd_base:
        cmd_base.write(cmd_base_content)


def check_module_requirements(api_module_config):
    """
    Expecting module descriptor file template:
    {
        "module_name": "$MODULE_NAME",
        "cli_path": "$MODULE_CLI_PATH",
        "mount_point": "$MOUNT_POINT",
        "dependencies": [
            {
                "module_name": "$MODULE_NAME_DEPENDENT_FROM",
                "min_version": "$MIN_ALLOWED_VERSION_OF_DEPENDED_MODULE"
            },
            ...
        ]
    }
    Property "dependencies" is optional, but if present - "module_name" in
    "dependencies"`s objects is required. Property "min_version" is optional
    """
    _LOG = get_logger(__name__)
    dependencies = api_module_config.get(DEPENDENCIES)
    if not dependencies:
        return
    candidate = api_module_config.get(MODULE_NAME_KEY)
    installed_packages = pkg_resources.working_set
    for item in dependencies:
        # check dependent module is installed
        dependent_module_name = item.get(MODULE_NAME_KEY)
        if not dependent_module_name:
            raise ModularApiConfigurationException(
                'Missing required property "module_name" in module '
                'descriptor file')
        installed_module_name = installed_packages.by_key.get(dependent_module_name)
        if not installed_module_name:
            raise ModularApiConfigurationException(
                f'Module "{dependent_module_name}" is marked as required for '
                f'"{candidate}" module. Please install "{dependent_module_name}" '
                f'first')
        # check major versions conflict
        dependency_min_version = item.get(MIN_VER)
        if not dependency_min_version:
            break
        installing_major_min_version = version.parse(dependency_min_version).major
        installed_major_version = installed_module_name.parsed_version.major
        if installing_major_min_version > installed_major_version:
            raise ModularApiConfigurationException(
                f'Module "{candidate}" requires a later major version of '
                f'"{dependent_module_name}". Please update "{dependent_module_name}" '
                f'to the latest version'
            )


@tracer.wrap()
def install_module(module_path):
    """
    :param module_path: the path to the installing module
    :return: none
    """
    _LOG = get_logger('install_module')
    path_to_setup_file_in_module = os.path.join(module_path, 'setup.py')
    if not os.path.isdir(module_path) or \
            not os.path.isfile(path_to_setup_file_in_module):
        incorrect_path_message = 'Provided path is incorrect or does not ' \
                                 'contain setup.py file'
        _LOG.error(incorrect_path_message)
        raise ModularApiBadRequestException(incorrect_path_message)

    with open(os.path.join(module_path, API_MODULE_FILE)) as file:
        api_module_config = json.load(file)

    _LOG.info('Going to install module prerequisites')
    if not all([key in api_module_config.keys()
                for key in DESCRIPTOR_REQUIRED_KEYS]):
        descriptor_key_absence_message = \
            f'Descriptor file must contains the following keys: ' \
            f'{", ".join(DESCRIPTOR_REQUIRED_KEYS)}'
        _LOG.error(descriptor_key_absence_message)
        raise ModularApiBadRequestException(descriptor_key_absence_message)

    check_module_requirements(api_module_config)

    modular_admin_path, _ = os.path.split(os.path.dirname(__file__))
    destination_folder = os.path.join(modular_admin_path, MODULES_DIR,
                                      api_module_config[MODULE_NAME_KEY])
    module_name = api_module_config[MODULE_NAME_KEY]
    path_to_module = os.path.join(MODULAR_ADMIN_ROOT_PATH, MODULES_DIR,
                                  module_name)
    if os.path.exists(path_to_module):
        _LOG.warning(f'The \'{module_name}\' module will be reinstalled')
        remove_tree(path_to_module)

    _LOG.info(f'Going to copy module files to {destination_folder}')
    copytree(
        module_path, destination_folder,
        ignore=ignore_patterns(
            '*.tox', 'build', '*.egg-info', '*.git', 'tests',
            'requirements-dev.txt', 'tox.ini', 'logs')
    )
    install_module_with_destination_folder(paths_to_module=destination_folder)

    _LOG.info(f'Copy {api_module_config[MODULE_NAME_KEY]} module '
              f'to {destination_folder}')
    mount_point = api_module_config[MOUNT_POINT_KEY]
    valid_methods = generate_valid_commands(
        destination_folder=destination_folder,
        path_to_scan=os.path.join(modular_admin_path, MODULES_DIR,
                                  api_module_config[MODULE_NAME_KEY],
                                  *api_module_config[CLI_PATH_KEY].split('/')),
        mount_point=mount_point,
        is_private_mode_enabled=False,
        path_to_setup_file_in_module=path_to_setup_file_in_module
    )
    web_service_cmd_base = os.path.join(modular_admin_path,
                                        'web_service',
                                        'commands_base.json')
    _LOG.info(f'Going to write generated meta to file {web_service_cmd_base}')
    write_generated_meta_to_file(path_to_file=web_service_cmd_base,
                                 mount_point=mount_point,
                                 groups_meta=valid_methods)
    return CommandResponse(
        message=f'{api_module_config[MODULE_NAME_KEY].capitalize()} '
                f'successfully installed')


def check_uninstall(api_module_config):
    """
    Expecting module descriptor file template:
    {
        "module_name": "$MODULE_NAME",
        "cli_path": "$MODULE_CLI_PATH",
        "mount_point": "$MOUNT_POINT",
        "dependencies": [
            {
                "module_name": "$MODULE_NAME_DEPENDENT_FROM",
            },
            ...
        ]
    }
    Property "dependencies" is optional, but if present - "module_name" in
    "dependencies"`s objects is required.
    """
    _LOG = get_logger(__name__)
    modules_path = Path(__file__).parent.parent / MODULES_DIR
    if not modules_path.exists():
        return
    conflict_modules_list = list()
    for module in modules_path.iterdir():
        api_file_path = module / API_MODULE_FILE
        if not api_file_path.exists():
            continue
        with open(api_file_path, 'r') as file:
            api_module_file = json.load(file)
            dependencies = list()
            if not api_module_file.get(DEPENDENCIES):
                continue
            for item in api_module_file.get(DEPENDENCIES):
                dependencies.append(item.get(MODULE_NAME_KEY))
            conflict_modules_list.append({
                f"{api_module_file.get(MODULE_NAME_KEY)}": dependencies
            })
    if not conflict_modules_list:
        return
    uninstall_candidate = api_module_config.get(MODULE_NAME_KEY)
    result_list = list()
    for conflict_item in conflict_modules_list:
        for k, v in conflict_item.items():
            if uninstall_candidate in v:
                result_list.append(k)
    if result_list:
        raise ModularApiConfigurationException(
            f'Module "{uninstall_candidate}" you are trying to uninstall is in '
            f'dependencies of the another module(s). Please uninstall '
            f'"{", ".join(result_list)}" module(s) first'
        )


@tracer.wrap()
def uninstall_module(module_name):
    """
    :param module_name: the name to the module to uninstalling
    :return: none
    """
    _LOG = get_logger(__name__)
    _LOG.info(f"Going to delete the '{module_name}' module")
    m3_modular_admin_dir, _ = os.path.split(os.path.dirname(__file__))

    module_descriptor_path = os.path.join(
        m3_modular_admin_dir, MODULES_DIR,
        module_name, API_MODULE_FILE)

    if not os.path.isfile(module_descriptor_path):
        incorrect_path_message = 'Provided path is incorrect or does ' \
                                 'not contain api_module.json file'
        _LOG.error(incorrect_path_message)
        raise ModularApiBadRequestException(incorrect_path_message)

    with open(module_descriptor_path) as file:
        api_module_config = json.load(file)

    check_uninstall(api_module_config)

    if not all(key in api_module_config.keys()
               for key in DESCRIPTOR_REQUIRED_KEYS):
        descriptor_key_absence_message = \
            f'Descriptor file must contains the following keys: ' \
            f'{", ".join(DESCRIPTOR_REQUIRED_KEYS)}'
        _LOG.error(descriptor_key_absence_message)
        raise ModularApiBadRequestException(descriptor_key_absence_message)

    web_service_cmd_base = os.path.join(MODULAR_ADMIN_ROOT_PATH,
                                        'web_service',
                                        'commands_base.json')

    mount_point = api_module_config[MOUNT_POINT_KEY]
    with open(web_service_cmd_base) as file:
        web_service_content = json.load(file)
    _LOG.info(f'Deleting the {mount_point} mount point from metadata')
    web_service_content.pop(mount_point, None)

    with open(web_service_cmd_base, 'w') as file:
        json.dump(web_service_content, file, indent=2)
    remove_tree(
        os.path.join(MODULAR_ADMIN_ROOT_PATH, MODULES_DIR, module_name))

    _LOG.info(f'The {module_name} module was successfully uninstalled')
    return CommandResponse(
        message=f'\'{module_name}\' successfully uninstalled')


def check_and_describe_modules(table_response):
    _LOG = get_logger(__name__)
    modules_path = Path(__file__).parent.parent / MODULES_DIR
    if not modules_path.exists():
        _LOG.warning(f'Directory \'{MODULES_DIR}\' does not exist')
        return CommandResponse(
            message=f'Missing \'{MODULES_DIR}\' by path \'{str(modules_path)}\'.'
                    f' Nothing to describe, please install any module first'
        )
    installed_modules_list = []
    for module in modules_path.iterdir():
        api_file_path = module / API_MODULE_FILE
        if not module.is_dir() or not api_file_path.exists():
            continue
        with open(api_file_path, 'r'):
            installed_modules_list.append(module.name)

    if not installed_modules_list:
        _LOG.warning('Modules are not installed')
        return CommandResponse(
            message='Can not find any installed module, nothing to describe'
        )

    modular_sdk_version = 'Modular-SDK: {0}'
    modular_cli_sdk_version = 'Modular-CLI-SDK: {0}'
    result_message = 'Installed modules:'
    pretty_table = list()
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(
        ["%s@%s" % (i.key, i.version) for i in installed_packages]
    )

    for module_name in installed_modules_list:
        for package_name in installed_packages_list:
            item_name, item_version = package_name.split('@')
            if item_name == 'modular-sdk':
                modular_sdk_version = modular_sdk_version.format(item_version)
            if item_name == 'modular-cli-sdk':
                modular_cli_sdk_version = modular_cli_sdk_version.format(item_version)
            if item_name == module_name:
                pretty_table.append(
                    {"Module name": module_name, "Version": item_version}
                )
                result_message += TOOL_VERSION_MAPPING.format(
                    tool=module_name.ljust(15), version=item_version)

    if modular_sdk_version == 'Modular-SDK: {0}':
        modular_sdk_version = 'Modular-SDK: Not installed'
    if modular_cli_sdk_version == 'Modular-CLI-SDK: {0}':
        modular_cli_sdk_version = 'Modular-CLI-SDK: Not installed'
    modular_version = f'Modular-API: {api_version}'
    if table_response:
        return CommandResponse(
            table_title=modular_version + '\n' + modular_sdk_version + '\n'
                        + modular_cli_sdk_version + '\n' + 'Installed modules',
            items=pretty_table)
    return CommandResponse(
        message=modular_version + '\n' + modular_sdk_version + '\n' + modular_cli_sdk_version
                + '\n' + result_message)
