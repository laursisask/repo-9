from dotenv import load_dotenv
from pathlib import Path
# looks awkward but where else we should load .env file so that all its vars
# appear in process's environment before all imports. Since
# modular_api_cli.modular_cli_group.modular.modular is the main CLI entrypoint
# for all commands, i assume this is a good place to load .env
root = Path(__file__).parent.parent
one = root / '.env'
two = root / 'modular_api' / '.env'
three = root / 'modular_api_cli' / '.env'
it = (load_dotenv(p, verbose=True) for p in (one, two, three))
next(filter(bool, it), None)
