# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beartype",
#     "tyro",
# ]
# ///
"""
Script to track progress towards 10K "actions" over the course of a year.

Examples:

10k add 5 pullups
10k add 30 meditation

10k progress pullups
10k progress meditation

"""

import contextlib
import dataclasses
import fcntl
import pathlib

import beartype
import tyro

scriptname = "tenthousand"

default_config_path = pathlib.Path.home() / f".local/config/{scriptname}/config.toml"


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Config:
    root: pathlib.Path = pathlib.Path.hom() / f".local/state/{scriptname}"

    @classmethod
    def from_path(cls, path: pathlib.Path):
        try:
            # Load config from TOML file.
            pass
        except FileNotFoundError as err:
            if path == default_config_path:
                # Inform the user that we are creating a new default config file here since it is missing.
                # Write a TOML file to path with default Config values.
                pass
            else:
                # Print an error and sys.exit with an error code.
                pass


@beartype.beartype
def add(
    count: int,
    task: str,
    /,
    config: pathlib.Path = default_config_path,
    init_task: bool = False,
):
    """
    Adds to the task file.

    Arguments:
        count: Number of actions completed.
        task: Which task the user is making progress on.
        config: Where the config file is stored.
        init_task: Whether to initialize a new file for a new task.
    """
    cfg = Config.from_path(config)

    # If task is not already tracked and init_task is true, create a new task file. Otherwise, ask the user if they want to create a new task file with interaction.
    task_file = cfg.root / task.with_suffix(".csv")
    # TODO

    with locked(task_file) as fd:
        # Write a new row to the CSV file with the timestamp and the number of actiosn taken.
        # TODO
        pass


@beartype.beartype
def progress():
    """
    Displays progress towards 10K.
    """
    breakpoint()


@contextlib.contextmanager
@beartype.beartype
def locked(filepath: pathlib.Path, mode: str = "w"):
    """Context manager for file locking.

    Creates an exclusive lock on <filepath>.lock while allowing concurrent reads of state_file.

    Usage:
        with locked(filepath) as fd:
            # Write to fd...

    Arguments:
        filepath: the file that you want to write to in a locked fashion.
        mode: the mode to open filepath in.
    """
    lock_file = filepath.with_suffix(filepath.suffix + ".lock")
    lock_file.touch(exist_ok=True)

    with open(lock_file, "r+") as lock_fd:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            # Open the state file in the requested mode
            with open(filepath, mode) as state_fd:
                yield state_fd
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    tyro.extras.subcommand_cli_from_dict({
        "add": add,
        "progress": progress,
    })
