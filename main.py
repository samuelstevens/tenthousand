# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beartype",
#     "tomli",
#     "tomli-w",
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
import sys
import tomli
import tomli_w

import beartype
import tyro

scriptname = "tenthousand"

default_config_path = pathlib.Path.home() / f".config/{scriptname}/config.toml"


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Config:
    root: pathlib.Path = pathlib.Path.home() / f".local/state/{scriptname}"

    @classmethod
    def from_path(cls, path: pathlib.Path):
        try:
            with open(path, "rb") as f:
                config_dict = tomli.load(f)
                return cls(**config_dict)
        except FileNotFoundError:
            if path == default_config_path:
                print(f"Creating new config file at {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                cfg = cls()
                config_dict = dataclasses.asdict(cfg)
                with open(path, "wb") as f:
                    tomli_w.dump(config_dict, f)
                return cls
            else:
                print(f"Error: Config file not found at {path}", file=sys.stderr)
                sys.exit(1)


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
    task_file = cfg.root / f"{task}.csv"

    if not task_file.exists():
        if init_task:
            print(f"Creating new task file for '{task}'")
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.touch()
        else:
            response = input(f"Task '{task}' doesn't exist. Create it? [y/N] ").lower()
            if response == "y":
                task_file.parent.mkdir(parents=True, exist_ok=True)
                task_file.touch()
            else:
                print("Aborted.", file=sys.stderr)
                sys.exit(1)

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
