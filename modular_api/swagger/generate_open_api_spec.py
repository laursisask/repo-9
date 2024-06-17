from modular_api.swagger.definition_templates import (
    get_open_api_spec_template, RESPONSES)


def resolve_parameter_type(param_type: str) -> str:
    """
    Changes the names of object types according to OpenAPI 3.0 types.
    Possible types in command{'enum', 'list', 'num', 'bool', 'str'} are
    converting into swagger types:
    {'string', 'number', 'integer','boolean' ,'array', 'object'}
    """
    if param_type in ['str', 'enum']:
        return 'string'
    elif param_type in ['list']:
        return 'array'
    elif param_type == 'bool':
        return 'boolean'
    elif param_type == "num":
        return 'number'
    return param_type


def resolve_group_name(command_path):
    if command_path.startswith('/v2'):
        command_path = command_path.replace('/v2', '')
    start_index = command_path.find('/') + 1
    end_index = command_path.find('/', 2)
    return command_path[start_index:end_index]


def generate_definition(commands_def, prefix) -> dict:
    """
    Generate config file(openapi_spec.yaml) for OpenAPI 3.0
    according to M3admin commands(commands_base.json)
    """

    result_paths = {}
    result_groups = []

    for command_name, command_meta in commands_def.items():
        description = command_meta.get('description')
        command_route = command_meta.get('route', {})
        method = command_route.get('method', '').lower()
        path = command_route.get('path')
        parameters = command_meta.get('parameters')
        get_param = []
        post_param = []
        # generate the parameters for "get", "delete"
        # requests from the command parameters
        if method in ["get", "delete"]:
            get_param = [{
                "name": parameter.get('name'),
                "required": parameter.get('required'),
                "description": parameter.get('description'),
                "in": "path",
                "schema": {"type": resolve_parameter_type(
                    parameter.get('type')
                )
                }} for parameter in parameters]
        # generate the schema and the example of body-requests
        # for "post", "put", "patch"
        # requests from command parameters
        elif method in ["post", "put", "patch"]:
            properties = {
                parameter.get("name"): {
                    'type': resolve_parameter_type(parameter.get('type')),
                    'description': parameter.get("description"),
                    'required': parameter.get("required")
                } for parameter in parameters
            }
            example = {parameter.get("name"): resolve_parameter_type(
                parameter.get('type')
            ) for parameter in parameters}
            post_param = {
                "description": "description of requestBody",
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": properties},
                        "example": example}
                }
            }
        # form path for config file
        group_name = resolve_group_name(command_path=command_name)
        command_definition = {
            path: {
                method: {
                    "summary": description,
                    "description": description,
                    "parameters": get_param,
                    "tags": [group_name],
                    "security": [{'BasicAuth': []}, {'BearerAuth': []}],
                    "requestBody": post_param,
                    "responses": RESPONSES
                }
            }
        }

        result_paths.update(command_definition)
        result_groups.append({'name': group_name})
    open_api_spec_template = get_open_api_spec_template(prefix=prefix)
    open_api_spec_template["tags"] = result_groups
    open_api_spec_template["paths"] = result_paths
    return open_api_spec_template
