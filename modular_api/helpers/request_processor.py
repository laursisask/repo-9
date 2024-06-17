import copy


def iterate_through_dict_values(result_meta, commands_meta, command_meta,
                                mount_point):
    # TODO why two copies?. Does not seem right
    for key, value in commands_meta.items():
        if isinstance(value, dict):
            if key.startswith('/'):
                mount_point = key
            elif value.get('route'):
                command_meta = value
            iterate_through_dict_values(result_meta, value, command_meta,
                                        mount_point)
        else:
            if key == 'path':
                copy_command_meta = copy.deepcopy(command_meta)
                copy_command_meta.update({'mount_point': mount_point})
                result_meta.update({value: copy_command_meta})
                command_meta = None


def generate_route_meta_mapping(commands_meta):
    command_meta = {}
    route_meta_mapping = {}
    mount_point = None
    iterate_through_dict_values(route_meta_mapping, commands_meta,
                                command_meta, mount_point)
    return route_meta_mapping
