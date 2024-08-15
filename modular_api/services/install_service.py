import json
import os
import ast
import sys
from pathlib import Path
import toml
import configparser
import subprocess
import shlex
from distutils.dir_util import remove_tree
from shutil import copytree, ignore_patterns
from unittest.mock import MagicMock
from importlib.metadata import distributions
from packaging import version
from ddtrace import tracer
from modular_api.helpers.constants import WINDOWS, LINUX, MODULES_DIR, \
    API_MODULE_FILE, MODULE_NAME_KEY, CLI_PATH_KEY, MOUNT_POINT_KEY, \
    TOOL_VERSION_MAPPING, DEPENDENCIES, MIN_VER
from modular_api.commands_generator import generate_valid_commands
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger
from modular_api.version import __version__

DESCRIPTOR_REQUIRED_KEYS = (CLI_PATH_KEY, MOUNT_POINT_KEY, MODULE_NAME_KEY)
MODULAR_ADMIN_ROOT_PATH = os.path.split(os.path.dirname(__file__))[0]
tracer.configure(writer=MagicMock())
_LOG = get_logger(__name__)


def install_module_with_destination_folder(paths_to_module: str):
    """
    Installing module by path
    :param paths_to_module: path to the modules
    :return: stdout, stderror of the installation process
    """
    if not paths_to_module:
        message = f"Path not found: {paths_to_module}"
        _LOG.error(message)
        sys.exit(message)
    if os.path.isfile(paths_to_module):
        message = f'The path {[paths_to_module]} to the module is file. ' \
                  f'Please specify the path to folder of the module which ' \
                  f'consist of setup.py.'
        _LOG.error(message)
        sys.exit(message)
    _LOG.info(f"Going to execute pip install command for {paths_to_module}")
    os_name = os.name
    command = f'pip install -e {paths_to_module}'
    if os_name == WINDOWS:
        with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
        ) as terminal_process:
            stdout, stderr = terminal_process.communicate()

    elif os_name == LINUX:
        with subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
        ) as terminal_process:
            stdout, stderr = terminal_process.communicate()
    else:
        message = f'The {os_name} OS is not supported by tool.'
        _LOG.error(message)
        sys.exit(message)
    if stdout is not None:
        stdout = stdout.decode('utf-8')
        _LOG.info(f"Out: {stdout}")
    if stderr is not None:
        stderr = stderr.decode('utf-8')
        _LOG.error(f"Errors: {stderr}")
        _LOG.info('Installation completed with errors')
        sys.exit(stderr)


def write_generated_meta_to_file(path_to_file, mount_point, groups_meta):
    if not os.path.isfile(path_to_file):
        cmd_base_content = json.dumps({mount_point: groups_meta},
                                      separators=(',', ':'))
    else:
        with open(path_to_file, 'r') as cmd_base:
            cmd_base_content = json.load(cmd_base)
        cmd_base_content.update({mount_point: groups_meta})
        cmd_base_content = json.dumps(cmd_base_content, separators=(',', ':'))

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
    dependencies = api_module_config.get(DEPENDENCIES)
    if not dependencies:
        return
    candidate = api_module_config.get(MODULE_NAME_KEY)
    installed_packages = {dist.metadata['Name']: dist for dist in distributions()}
    for item in dependencies:
        # check dependent module is installed
        dependent_module_name = item.get(MODULE_NAME_KEY)
        if not dependent_module_name:
            message = 'Missing required property "module_name" in module ' \
                      'descriptor file'
            _LOG.error(message)
            sys.exit(message)
        installed_module_name = installed_packages.get(dependent_module_name)
        if not installed_module_name:
            message = f'Module "{dependent_module_name}" is marked as ' \
                      f'required for "{candidate}" module. Please install ' \
                      f'"{dependent_module_name}" first'
            _LOG.error(message)
            sys.exit(message)
        # check major versions conflict
        dependency_min_version = item.get(MIN_VER)
        if not dependency_min_version:
            break
        installing_major_min_version = version.parse(dependency_min_version).major
        installed_major_version = version.parse(installed_module_name.version).major
        if installing_major_min_version > installed_major_version:
            message = f'Module "{candidate}" requires a later major version ' \
                      f'of "{dependent_module_name}". Please update ' \
                      f'"{dependent_module_name}" to the latest version'
            _LOG.error(message)
            sys.exit(message)


def extract_module_requirements_setup_py(module_path: str) -> list[str]:
    """
    Extracts the dependencies from the setup.py file
    :param module_path: path to the setup.py file
    :return: a list of strings, where each string represents a dependency
    """
    # get dependencies for module to be installed
    module_dependencies = []
    with open(module_path) as module_file:
        parsed = ast.parse(module_file.read())
    for node in parsed.body:
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if node.value.func.id != "setup":
            continue
        for keyword in node.value.keywords:
            if keyword.arg == "install_requires":
                module_dependencies = ast.literal_eval(keyword.value)
    return module_dependencies


def extract_module_requirements_setup_cfg(module_path: str) -> list[str]:
    """
    Extracts the dependencies from a setup.cfg file
    :param module_path: path to the setup.cfg file
    :return: a list of strings, where each string represents a dependency
    """
    config = configparser.ConfigParser()
    config.read(module_path)
    try:
        module_dependencies = config.get(
            'options', 'install_requires'
        ).split('\n')
        module_dependencies = [
            dependency for dependency in module_dependencies if dependency
        ]
    except (configparser.NoSectionError, configparser.NoOptionError):
        module_dependencies = []

    return module_dependencies


def extract_module_requirements_toml(module_path: str) -> list[str]:
    """
    Extracts the dependencies from a pyproject.toml file
    :param module_path: path to the pyproject.toml file
    :return: a list of strings, where each string represents a dependency
    """
    # get dependencies for module to be installed
    with open(module_path, 'r') as module_file:
        parsed = toml.load(module_file)
        module_dependencies = parsed['project']['dependencies']
    return module_dependencies


def check_module_requirements_compatibility(
    module_dependencies: list[str], module_name: str
):
    """
    Checks if the version requirements for the dependencies are compatible with
    the modules currently installed in the API's dependency list
    :param module_dependencies: a list of module dependencies
    :param module_name: the name of the module whose dependencies are being
    checked
    :return: None, but raises SystemExit if a specific version is not provided
    or there is a version conflict
    """
    # get current dependencies list for Modular-API
    installed_packages = {
        dist.metadata['Name']: dist.version for dist in distributions()
    }
    modular_api_dependencies = [
        f"{name}=={ver}" for name, ver in installed_packages.items()
    ]

    # check sticking for a specific version
    if not module_dependencies:
        return
    for req in module_dependencies:
        if "[" in req:
            continue
        # todo refactor - stick to major version
        if ">=" in req:
            continue
        if len(req.split('==')) == 1:
            message = (
                f'Please add a specific version for package \'{req}\' in module'
                f' \'{module_name}\''
            )
            _LOG.error(message)
            sys.exit(message)

    # check versions compatibility
    for mod_req in module_dependencies:
        for api_req in modular_api_dependencies:
            if "[" in mod_req:
                continue
            try:
                # todo refactor - stick to major version
                mod_req_name, mod_req_ver = mod_req.split('==')
                api_req_name, api_req_ver = api_req.split('==')
            except ValueError:
                continue
            if mod_req_name != api_req_name:
                continue
            version_to_install = version.parse(mod_req_ver)
            version_should_be = version.parse(api_req_ver)
            if version_to_install != version_should_be:
                message = f'Modular-API has \'{version_should_be}\' version ' \
                          f'of the \'{api_req_name}\', but module ' \
                          f'\'{module_name}\' stick to \'{version_to_install}\' ' \
                          f'version. Please resolve version conflict.'
                _LOG.error(message)
                sys.exit(message)


@tracer.wrap()
def install_module(module_path):
    """
    :param module_path: the path to the installing module
    :return: none
    """
    extract_dependencies_func_map = {
        'setup.py': extract_module_requirements_setup_py,
        'setup.cfg': extract_module_requirements_setup_cfg,
        'pyproject.toml': extract_module_requirements_toml
    }
    setup_files = ["pyproject.toml", "setup.cfg", "setup.py"]
    _LOG.info(f'Going to install module from path: {module_path}')
    if not os.path.isdir(module_path):
        incorrect_path_message = (
            'Provided path is incorrect. It should be a directory.'
        )
        _LOG.error(incorrect_path_message)
        sys.exit(incorrect_path_message)

    with open(os.path.join(module_path, API_MODULE_FILE)) as file:
        api_module_config = json.load(file)

    _LOG.info('Checking module descriptor properties')
    if not all(
        [key in api_module_config.keys() for key in DESCRIPTOR_REQUIRED_KEYS]
    ):
        descriptor_key_absence_message = \
            f'Descriptor file must contains the following keys: ' \
            f'{", ".join(DESCRIPTOR_REQUIRED_KEYS)}'
        _LOG.error(descriptor_key_absence_message)
        sys.exit(descriptor_key_absence_message)

    # Check each setup file by priority
    for setup_file in setup_files:
        setup_file_path = os.path.join(module_path, setup_file)
        if not os.path.isfile(setup_file_path):
            continue  # Skip if file doesn't exist

        _LOG.info('Checking module requirements compatibility')
        try:
            _LOG.info(f"Reading dependencies from: {setup_file}")
            extract_func = extract_dependencies_func_map[setup_file]
            module_dependencies = extract_func(
                module_path=setup_file_path
            )
        except KeyError:
            _LOG.error(f'Unsupported setup file: {setup_file}')
            sys.exit(f'Unsupported setup file: {setup_file}')

        check_module_requirements_compatibility(
            module_dependencies=module_dependencies,
            module_name=api_module_config.get('module_name')
        )
        # Found valid setup file, break the loop
        _LOG.info(f"Successfully loaded dependencies from {setup_file}")
        break
    else:
        _LOG.error("No valid setup file found")
        sys.exit("No valid setup file found")

    _LOG.info('Checking module dependencies')
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

    copytree(
        module_path, destination_folder,
        ignore=ignore_patterns(
            '*.tox', 'build', '*.egg-info', '*.git', 'tests',
            'requirements-dev.txt', 'tox.ini', 'logs')
    )
    install_module_with_destination_folder(paths_to_module=destination_folder)

    _LOG.info(f'Copy {api_module_config[MODULE_NAME_KEY]} module files '
              f'to {destination_folder}')
    mount_point = api_module_config[MOUNT_POINT_KEY]
    valid_methods = generate_valid_commands(
        destination_folder=destination_folder,
        path_to_scan=os.path.join(modular_admin_path, MODULES_DIR,
                                  api_module_config[MODULE_NAME_KEY],
                                  *api_module_config[CLI_PATH_KEY].split('/')),
        mount_point=mount_point,
        is_private_mode_enabled=False,
        path_to_setup_file_in_module=setup_file_path
    )
    web_service_cmd_base = os.path.join(modular_admin_path,
                                        'web_service',
                                        'commands_base.json')
    _LOG.info(f'Updating commands meta file by path: {web_service_cmd_base}')
    write_generated_meta_to_file(path_to_file=web_service_cmd_base,
                                 mount_point=mount_point,
                                 groups_meta=valid_methods)
    message = f'{api_module_config[MODULE_NAME_KEY].capitalize()} ' \
              f'successfully installed'
    _LOG.info(message)
    return CommandResponse(message=message)


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
        message = f'Module "{uninstall_candidate}" you are trying to ' \
                  f'uninstall is in dependencies of the another module(s). ' \
                  f'Please uninstall "{", ".join(result_list)}" module(s) first'
        _LOG.error(message)
        sys.exit(message)


@tracer.wrap()
def uninstall_module(module_name):
    """
    :param module_name: the name to the module to uninstalling
    :return: none
    """
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
        sys.exit(descriptor_key_absence_message)

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


def check_and_describe_modules(
        table_response: bool | None = None,
        json_response: bool | None = None,
) -> CommandResponse:
    if table_response and json_response:
        _LOG.error('Wrong parameters passed')
        raise ModularApiBadRequestException(
            'Please specify only one parameter - table or json')
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
    installed_packages = {dist.metadata['Name']: dist.version for dist in distributions()}
    installed_packages_list = sorted(
        ["%s@%s" % (name, version) for name, version in installed_packages.items()]
    )

    for module_name in installed_modules_list:
        for package_name in installed_packages_list:
            item_name, item_version = package_name.split('@')
            if item_name == 'modular_sdk':
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
    modular_version = f'Modular-API: {__version__}'

    if json_response:
        modular_sdk_item = modular_sdk_version.split(':')[0].lower()
        modular_sdk_item_ver = modular_sdk_version.split(':')[1].lower()
        modular_cli_sdk_item = modular_cli_sdk_version.split(':')[0].lower()
        modular_cli_sdk_item_ver = modular_cli_sdk_version.split(':')[1].lower()
        result_json = {
            'modular': __version__,
            modular_sdk_item: modular_sdk_item_ver.strip(),
            modular_cli_sdk_item: modular_cli_sdk_item_ver.strip()
        }
        for item in pretty_table:
            item_name = item.get('Module name')
            item_vers = item.get('Version')
            result_json.update({item_name: item_vers})
        return CommandResponse(
            message=json.dumps(result_json, indent=4)
        )

    if table_response:
        return CommandResponse(
            table_title=modular_version + '\n' + modular_sdk_version + '\n'
                        + modular_cli_sdk_version + '\n' + 'Installed modules',
            items=pretty_table)
    return CommandResponse(
        message=modular_version + '\n' + modular_sdk_version + '\n' + modular_cli_sdk_version
                + '\n' + result_message)
