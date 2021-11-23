import sys

from todd import subcommands
from todd.index import pkg_index_exists
from argparse import ArgumentParser



def main() -> bool:
    parser = ArgumentParser(description="ToddLinux Builder.")
    parser.add_argument("subcommand", help="subcommand to do", type=str)
    parser.add_argument("subcommand_args", help="subcommand args", nargs='*')

    args = parser.parse_args()
    subcommand_name = args.subcommand
    subcommand_args = args.subcommand_args

    if not pkg_index_exists("/"):
        print("Package index doesnt exist.")
        return False
    
    if not subcommand_name in subcommands.SUBCOMMANDS:
        print("No such subcommand:", subcommand_name)
        return False

    subcommand = subcommands.SUBCOMMANDS[subcommand_name]
    if not subcommand.validate_args(subcommand_args):
        return False

    subcommand.handle(args.subcommand_args)

    return True

if __name__ == '__main__':
    sys.exit(0 if main() else 1)