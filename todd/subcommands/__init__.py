__all__ = [ "subcommand" ]

from .subcommand import Subcommand
from . import blame

SUBCOMMANDS = {
    "blame": Subcommand(blame.blame_args_validator, blame.blame_handler)
}