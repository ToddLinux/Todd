from .blame import *
from .subcommand import *

SUBCOMMANDS = {"blame": Subcommand(blame.blame_args_validator, blame.blame_handler)}
