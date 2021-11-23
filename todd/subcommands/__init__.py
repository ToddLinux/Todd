from .subcommand import *
from .blame import *

SUBCOMMANDS = {
    "blame": Subcommand(blame.blame_args_validator, blame.blame_handler)
}