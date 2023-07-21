CHANGELOG

## [2.2.17] - 2023-07-20
* improved checking of modules dependencies while installation/uninstallation 

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
