CHANGELOG


# [4.0.5] - 2024-06-25
* Update library version from `modular-sdk==5.1.1` to `modular-sdk>=5.1.3,<6.0.0`
* Update library version from `typing-extensions==4.10.0` to `typing-extensions>=4.10.0,<5.0.0`

# [4.0.4] - 2024-06-19
* Add fixed version `tenacity==8.4.1` in requirements.txt to resolve import issue

# [4.0.3] - 2024-06-10
* Add error handling to return exit code 1 when `modular_api_cli` command execution fails
* Update parameter handling for `--json` and `--table` in commands:
  * `modular describe`, `modular audit`, `user get_meta`
  * `user describe`, `policy describe`

# [4.0.2] - 2024-04-29
* Fix meta keys validation logic to operate independent of file formatting

# [4.0.1] - 2024-04-22
* Fix `internal server error` when trying to `login` without a `username` (in SaaS mode)

# [4.0.0] - 2024-03-21
- remove tinydb, move to mongodb
- rewrite wsgi application builder
- make swagger open
- remove not used code and not used libs
- refactor slightly
- add ability to start gunicorn server, move server start command to cli
- remove `startup_config.json`. Replace it with cli parameters and environment variables. Add `.env` file support.

# [3.3.21] - 2024-04-09
* Fix issues related to CLI version WARNING
  * Resolve bug associated with CLI version WARNING
  * Adjust `@property` decorator usage. Now accessible as an attribute, not a 
  method. Make necessary replacements where required

# [3.3.19] - 2024-03-25
* Fix an issue where the last line of the error message was lost in the
  `exception_log` function.
* Updates related to `ModularUser` include:
  * Update `meta` field to now store two types of meta: `allowed_values` and `aux_data`.
  * Include `--meta_type` parameter in `modular user set_meta_attribute` command.
    This parameter allows two types, `allowed_values` (set as `default` if this
    flag is not provided) and `aux_data`.
  * Add sorting to `meta` field in `ModularUser` table to ensure consistent
    order, preventing different hashes generation from different orders.
    This new function sorts dictionaries and lists at any depth level.
  * Add `aux_data` to `thread-local storage`. Retrieve this from the db using
    the user located in `ModularUser.meta`.
  * Update commands to ensure compatibility with changes related to `meta`:
    * `set_meta_attribute`, `update_meta_attribute`, `delete_meta_attribute`,
      `reset_meta`, `get_meta`

# [3.3.18] - 2024-03-11
* `swagger-ui-py` from 21.12.8 to 23.9.23
* Implement fixes and improvements for `swagger-ui`:
  * The logic for `login`:
    * Unauthorized users are now provide with an empty `swagger.json` file
    * Generate new `swagger.json` instead of new `page`
  * Add middleware to capture all `swagger.json` files
  * Imports for exceptions

# [3.3.17] - 2024-03-18
* hide error logs when starting server on MacOS
* remove `PyYAML` from setup.py
* Fix an issue that occurred while saving `meta` for `ModularUser` in on-prem mode
* Add `meta` to `thread local storage`, which contains the `ModularUser` field `meta`
* Add `service_name` and `service_display_name` in the allowed values for `meta`
* Add sorting of the `meta` field in the `ModularUser` table to ensure a
consistent order, as different orders can generate different hashes

# [3.3.16] - 2024-03-01
* Add a new class `FileHandlerManager` to the log_helper file to prevent the
`Too Many Open Files` error

# [3.3.15] - 2024-02-28
* Implement throttle manager: `Too Many Requests`
* Add a new value `"limit_api_call": 30` to `startup_config.json`, where `30`
represents the maximum number of calls per second. If no value is provided, the
default is set to `10`

# [3.3.14] - 2024-02-28
* Fix issue: `Too many open files`

# [3.3.13] - 2024-02-26
* Add the ability to install modules inside `modular-api` using `setup.cfg` and
`pyproject.toml`

# [3.3.12] - 2023-12-07
* Json flag added for next commands:
`user describe`, `user get_meta`, `policy describe`, `group describe`, `audit`

# [3.3.11] - 2023-12-07
* Update `exception_log()` to use a `with` block when opening the `LOG_FILE`,
ensuring the file gets properly closed after operations are completed.
* Fix file handling in `check_module_requirements_compatibility()`. Previously,
the `module_path` file was opened for analysis but not closed properly.

# [3.3.10] - 2023-11-03
* Implemented proper bool type option processing in direct API requests

# [3.3.9] - 2023-11-01
* Fix command `modular user add` if the password was entered by the user then
  it will not be displayed

# [3.3.8] - 2023-11-01
* Fix flag value resolving

# [3.3.7] - 2023-10-31
* Fix modules installation issue

# [3.3.6] - 2023-10-30
* Implemented proper bool type command option processing.

# [3.3.5] - 2023-10-25
* Fix setuptools deprecation warning. Change `pkg_resources` to `importlib.metadata`

# [3.3.4] - 2023-10-25
* Standardized name of keys of stats item
* Added mechanism of native module name inclusion to stats item.

# [3.3.3] - 2023-10-18
* Changed statistic item ID generation method.
* Verification script adapted to new item ID generation method.

# [3.3.2] - 2023-10-17
* Reduce calls to modular_api_log from modular_api_cli
* Add environment variables to configure separate log paths for modular_api and
modular_api_cli logs

# [3.3.1] - 2023-10-05
* Resolve payload, handle empty exec_status in save_stats method

# [3.3.0] - 2023-10-04
* Add `modular user change_username` command

# [3.2.1] - 2023-10-04
* Minimal allowed cli version raised to 2.0

# [3.2.0] - 2023-10-03
* Save modular user username to modular_sdk thread-local storage

## [3.1.0] - 2023-09-29
* Implemented async jobs registration

## [3.0.1] - 2023-09-26
* Add library `typing_extensions==4.7.1` in setup.py
* Fix typo: library `pydantic` used twice in setup.py

# [3.0.0] - 2023-09-25
* Update libraries to support Python 3.10:
  * `Beaker` from 1.11.0 to 1.12.1
  * `botocore` from 1.27.38 to 1.29.80
  * `bottle` from 0.12.19 to 0.12.25
  * `ddtrace` from 0.58.5 to 0.61.5
  * `MarkupSafe` from 2.1.1 to 2.1.3
  * `prettytable` from 3.2.0 to 3.9.0
  * `Pillow` from 8.3.1 to 10.0.0
  * `pydantic` from 1.9.1 to 1.10.2
  * `PyJWT` from 2.4.0 to 2.8.0
  * `pyparsing` from 3.0.9 to 3.1.1
  * `PyYAML` from 6.0 to 6.0.1
  * `tenacity` from 8.0.1 to 8.2.3
  * `typing_extensions` from 4.3.0 to 4.7.1
  * `urllib3` from 1.26.11 to 1.26.16
  * `setuptools` from 60.6.0 to 68.2.1
  * `wcwidth` from 0.2.5 to 0.2.6

## [2.2.32] - 2023-09-14
* Fix bug related to consistency in usage statistic report

## [2.2.31] - 2023-09-01
* Update setup requirements

## [2.2.30] - 2023-08-31
* Refactoring response during module install/uninstall - exit status code "1" instead 
of exception raising [CICD-team request]

## [2.2.29] - 2023-08-31
* Fix minor issues with logs
* Handle unexpected click exceptions from modules proxy their responses to 
  modular-cli [EPMCEOOS-5021]

## [2.2.28] - 2023-08-30
* Split logs for api-service and api-cli [EPMCEOOS-5024]

## [2.2.27] - 2023-08-28
* Fix auto relogin bug

## [2.2.26] - 2023-08-28
* Fix write permissions issue while saving statistic report in command `modular get_stats` 

## [2.2.25] - 2023-08-23
* Fix bug during modules installation [EPMCEOOS-5042]

## [2.2.24] - 2023-08-21
* Add version compatibility checking between Modular-API dependencies and module 
to be installed to API [EPMCEOOS-5042]

## [2.2.23] - 2023-08-11
* Add ability to collect usage statistic [EPMCEOOS-4974]

## [2.2.22] - 2023-08-02
* Add ability to set custom log path by environment variable `SERVICE_LOGS` [EPMCEOOS-5022]

## [2.2.21] - 2023-07-31
* Fix an issue with path to modules directory for `/version` resource

## [2.2.20] - 2023-07-27
* Add ability to show response in JSON format for command `modular describe`

## [2.2.19] - 2023-07-26
* Add ability to set up custom path to DB files in On-Premises mode.

## [2.2.18] - 2023-07-24
* Change entry point for console script from `m3modular` to `modular`, 
fix "modules" dir path resolving

## [2.2.17] - 2023-07-20
* Improved checking of modules dependencies while installation/uninstallation 

## [2.2.16] - 2023-07-11
* Integrate `modular-sdk` and `modular-cli-sdk` instead of `mcdm` usage 

## [2.2.15] - 2023-06-08
* Fix the bug in case if warnings are in command response, but no version warnings. 
This bug affects third party api-clients usage with Modular-API

## [2.2.14] - 2023-06-08
* Update README.md file for Open Source
* Add description of the installed version of the MCDM CLI SDK in `m3modular describe` 
command

## [2.2.13] - 2023-06-02
* Fix a bug in case if whitespace symbol was received in GET request
* Rework `m3modular describe` command [EPMCEOOS-4913]

## [2.2.12] - 2023-05-25
* Fix a bug with auto login in case if invalid headers received

## [2.2.11] - 2023-05-23
* Fix an issue with error response from billing adapters
* Fix a bug when you could not start the server from any folder

## [2.2.10] - 2023-05-11
* Fix the bug with automated re-login in case if user will use "Basic" auth type 
instead of "Bearer"

## [2.2.9] - 2023-05-03
* Implement automated re-login for Modular-CLI users. Make JWT token expired for
api-clients users in case if commands meta file has changed [EPMCEOOS-4864]

## [2.2.8] - 2023-05-02
* Rework CRUD commands for user-group-policy management:
  * fix commands help description
  * rewrite response messages for different cases
  * fix issues when non-existed groups or policies could be added
  * fix issue when admin can not remove policy attached to the removed group
[EPMCEOOS-4862]

## [2.2.7] - 2023-04-19
* Prettify `m3modular describe` response for `--table` flag [Python-team request] 
* Add handling of expired JWT token case

## [2.2.6] - 2023-04-11
* Keep module-specific extra attributes in response

## [2.2.5] - 2023-04-10
* Update error message in case if user credentials are expired

## [2.2.4] - 2023-04-07
* Pass modular user's username to click context in a subordinate module

## [2.2.3] - 2023-04-05
* Add commands meta skipping by default for request to "/login". Remove `warnings` 
property from "/login" response if no warnings exist.
* Raise minimal allowed Modular-CLI version to `1.2`

## [2.2.2] - 2023-04-04
* Remove salt from jwt token and fix expiration

## [2.2.1] - 2023-04-04
* Rewritten response processor so that it could keep extra attributes
* Fix a bug with resolving `modules` folder path;

## [2.2.0] - 2023-03-24
* Implement RBAC v2 for policy management [EPMCEOOS-4802]

## [2.1.11] - 2023-03-31
* Fix an issue associated with incorrect username resolving for audit records in 
case if m3admin works as a part of Modular-API [EPMCEOOS-4822]

## [2.1.10] - 2023-03-30
* Update README.md file [EPMCEOOS-4804]

## [2.1.9] - 2023-03-24
* Raise PynamoDB version to `5.3.2` due to MCDM sdk 1.4.0

## [2.1.8] - 2023-03-08
* Add ability to upload *.pfx file formats

## [2.1.7] - 2023-02-28
* Fix an error associated with invalid resolving user permissions [EPMCEOOS-4733] 

## [2.1.6] - 2023-01-30
* Add ability to restrict module root commands by policies [EPMCEOOS-4733] 

## [2.1.5] - 2023-01-30
* Improve group/policy consistency check mechanism [EPMCEOOS-4730]

## [2.1.4] - 2023-01-30
* Add ability to write full exception traceback to log file 

## [2.1.3] - 2023-01-23
* Remove handling "0" as a successful status code due to changes on the m3-server
[EPMCEOOS-4645]

## [2.1.2] - 2023-01-13
* Fix the bug associated with incorrect response building in case if warnings were
  added in response body

## [2.1.1] - 2022-11-24
* Fix an error associated with inability process incoming requests in case 
`Cli-Version` header does not specified

## [2.1.0] - 2022-11-24
* Implement version compatibility check

## [2.0.15] - 2022-11-24
* Add new success status code "0" for compatibility with m3-reseller-cli-module

## [2.0.14] - 2022-11-10
* Add new set of commands for managing user `meta` attribute [SFTGMSTR-6477]:
  * `m3modular user set_meta attribute`
  * `m3modular user update_meta_attribute`
  * `m3modular user delete_meta_attribute`
  * `m3modular user reset_meta`
  * `m3modular user get_meta`

## [2.0.13] - 2022-11-09
* Fix an error associated with inability to execute component`s commands with 
  parameter value which added to user meta information

## [2.0.12] - 2022-09-30
* Fix an error associated with inability to properly calculate user item hash 
in case meta information attached to user [SFTGMSTR-6453]

## [2.0.11] - 2022-09-30
* Added ability to validate received values from request body by comparing 
them with user meta [SFTGMSTR-6453]

## [2.0.10] - 2022-10-27
* Deleted duplicate terminal messages in m3modular commands

## [2.0.9] - 2022-09-30
* Added the processing of the `LOG_PATH` environment variable for storing 
  logs by the custom path. Changed the default path of the storing logs 
  on the Linux-based VMs to the 
  `/var/log/<app_name>/<user_name>/<app_name.log>`path. [SFTGMSTR-6234]

# [2.0.9] - 2022-09-29
* Fix a bug associated with inability of correct work flow in policy simulator
  in case of checking actions from components subgroups [SFTGMSTR-6321]

# [2.0.8] - 2022-09-29
* Extended help message to `m3modular policy_simulator` command with usages 
examples
* Extend logging for services which processed groups, users and policies [SFTGMSTR-6320]

# [2.0.7] - 2022-09-15
* Improve interaction with root commands by moving them to upper level during 
commands meta generation

# [2.0.6] - 2022-09-09
* Implemented `m3modular policy_simulator` command which allows indicating 
user/group/policy command or resource availability

# [2.0.5] - 2022-08-17
* Fixed datetime resolving in "onprem" mode for TinyDB instance

# [2.0.4] - 2022-08-16
* Fixed processing the temp_file path in case transferring the file from the CLI side
* Delete group `audit` and moved from it command `audit describe`. Rename
  `m3modular audit describe` to `m3modular audit`.

# [2.0.3] - 2022-08-09
* Improved `m3modular audit describe` command - all parameters are made optional

# [2.0.2] - 2022-08-03
* Fix error associated with conflict in namespace during of additional modules 
  installation - `ModuleNotFoundError`

# [2.0.1] - 2022-07-28
* Implemented command which allows manage audit [SFTGMSTR-6120]:
  * `m3modular audit describe`
* Removed `--force-reinstall` flag for Linux platforms due to errors with 
  installing modules
* The logging of the module uninstallation operation was extended

# [2.0.0] - 2022-06-27
* Implemented commands which allows manage group entity [SFTGMSTR-6167]:
  * `m3modular group add`
  * `m3modular group add_policy`
  * `m3modular group delete_policy`
  * `m3modular group describe`
  * `m3modular group delete`
* Implemented commands which allows manage policy entity [SFTGMSTR-6166]:
  * `m3modular policy add`
  * `m3modular policy update`
  * `m3modular policy describe`
  * `m3modular policy delete`
* Implemented commands which allows manage user entity [SFTGMSTR-6167]:
  * `m3modular user add`
  * `m3modular user update`
  * `m3modular user describe`
  * `m3modular user delete`
* Implemented environment dependent data storage [SFTGMSTR-6119]:
  * `TinyDB` for `onprem` and `private` mode which stores data in the following path: `~/.m3modular/databases`
  * `DynamoDB` for `saas` mode
* Improved the way users credentials are stored [SFTGMSTR-6118]

# [1.0.14] - 2022-06-27
* Fix an error associated with incorrect policy files validation [SFTGMSTR-5943]

# [1.0.13] - 2022-06-27
* Fix an error associated with ability to get access without authentication 
  to SwaggerUI if link is known [SFTGMSTR-5946]
* Update README.md file [SFTGMSTR-5980]

# [1.0.12] - 2022-06-22
* Added ability to provide password during user creation with `m3modular user add` 
  command [SFTGMSTR-6036]
* Fix an error associated with inability to access user policy files before 
  OpenAPI specification generation [SFTGMSTR-5946]

# [1.0.11] - 2022-06-21
* Implemented ability to generate SwaggerUI page for each group based on it 
  permissions [SFTGMSTR-5946]
* Added the` --version` parameter for version determination
* Fix error associated with unnecessary retrieving credentials for AWS
  when generating commands meta
* Fix an error associated with invalid routing when url prefix specified [SFTGMSTR-5946]

# [1.0.10] - 2022-06-17
* Implemented `hidden` parameters which allows securing sensitive 
  information in logs [SFTGMSTR-5931]

# [1.0.9] - 2022-06-17
* Fix an issue with installing dependencies during module installation/reinstallation
  depending on system type (Windows/Linux)
* Fix an issue with installing dependencies during module installation/reinstallation
* Add consistency and version checking during installing/uninstalling of modules
  [SFTGMSTR-6045]

# [1.0.8] - 2022-06-08
* Fix incorrect resolving of secure parameter
* Add policy file validation [SFTGMSTR-5943]
* Added ability to authenticate through JWT 

# [1.0.7] - 2022-06-02
* Hide the trace in the log file in case of an exception occurs 
  and show a standard error message, [SFTGMSTR-5981]

# [1.0.6] - 2022-05-18
* Fix meta generator for BA when parsing secure parameters

# [1.0.5] - 2022-05-10
* Add error message to `m3modular user delete` command in case provided 
  user not exists
* Add error message to `m3modular user delete` command in case provided user 
  already added to trusted
* Change `m3modular user update_group` command:
  * Rename from  `update_group` to `update`
  * Add param `--password` and `--force`, that allows to change user password


# [1.0.4] - 2022-04-22
* Add ability to process file content in passed parameters and redirect them 
  to module handler

# [1.0.3] - 2022-04-22
* Add the following commands to manage user:
  * `m3modular user add`
  * `m3modular user delete`
  * `m3modular user update_policy`

# [1.0.2] - 2022-04-18
* Handled errors during installing process

# [1.0.1] - 2022-04-15
* Fix incorrect resolving of boolean attributes

# [1.0.0] - 2022-03-08
* Release of m3-modular-admin versioning
