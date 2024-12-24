#!/usr/bin/env -S uv run --script --quiet
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
import csv
import datetime
import sys
import tomli
import tomli_w
import difflib

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
                # Convert string path back to Path object
                config_dict["root"] = pathlib.Path(config_dict["root"])
                return cls(**config_dict)
        except FileNotFoundError:
            if path == default_config_path:
                print(f"Creating new config file at {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                cfg = cls()
                config_dict = dataclasses.asdict(cfg)
                # Convert Path objects to strings for TOML serialization
                config_dict["root"] = str(config_dict["root"])
                with open(path, "wb") as f:
                    tomli_w.dump(config_dict, f)
                return cfg
            else:
                print(f"Error: Config file not found at {path}", file=sys.stderr)
                sys.exit(1)


@beartype.beartype
class TaskNotFoundError(Exception):
    """Raised when attempting to load a task that doesn't exist"""

    def __init__(self, task: str, matches: list[str]):
        self.task = task
        self.matches = matches
        super().__init__(f"Task '{task}' not found")


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Task:
    name: str
    data: list[tuple[datetime.datetime, int]]

    @classmethod
    def load(cls, cfg: Config, name: str) -> "Task":
        """Load an existing task from disk.

        Arguments:
            cfg: The configuration object
            name: Name of the task to load

        Returns:
            The loaded Task

        Raises:
            TaskNotFoundError: If the task doesn't exist
        """
        task_file = cfg.root / f"{name}.csv"

        if not task_file.exists():
            # Get list of similar tasks for the error message
            existing_tasks = [f.stem for f in cfg.root.glob("*.csv")]
            matches = difflib.get_close_matches(name, existing_tasks, n=3, cutoff=0.6)
            raise TaskNotFoundError(name, matches)

        data = []
        with open(task_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append((
                    datetime.fromisoformat(row["timestamp"]),
                    int(row["count"]),
                ))

        return cls(name, data)

    @classmethod
    def new(cls, cfg: Config, name: str):
        """Return a new task stored on disk."""
        task_file = cfg.root / f"{name}.csv"
        task_file.parent.mkdir(parents=True, exist_ok=True)

        data = []
        if not task_file.exists():
            with locked(task_file, "w") as fd:
                writer = csv.writer(fd)
                writer.writerow(["timestamp", "count"])
            print(f"Created new task file for '{name}'")
        else:
            with open(task_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append((
                        datetime.fromisoformat(row["timestamp"]),
                        int(row["count"]),
                    ))

        return cls(name, data)


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

    task_file = get_task(task, cfg, init=init_task)
    task_file.parent.mkdir(parents=True, exist_ok=True)
    with locked(task_file, "a") as fd:
        # Check if file is empty (new file)
        fd.seek(0, 2)  # Seek to end
        if fd.tell() == 0:  # File is empty
            if init_task:
                print(f"Creating new task file for '{task}'")
                writer = csv.writer(fd)
                writer.writerow(["timestamp", "count"])
            else:
                response = input(
                    f"Task '{task}' doesn't exist. Create it? [y/N] "
                ).lower()
                if response == "y":
                    writer = csv.writer(fd)
                    writer.writerow(["timestamp", "count"])
                else:
                    print("Aborted.", file=sys.stderr)
                    sys.exit(1)

        # Write a new row to the CSV file with the timestamp and count
        writer = csv.writer(fd)
        timestamp = datetime.now(tz=datetime.timezone.utc).isoformat()
        writer.writerow([timestamp, count])


@beartype.beartype
def progress(task: str, /, config: pathlib.Path = default_config_path):
    """
    Displays progress towards 10K.

    Shows current progress, expected progress, and required daily average to reach 10K.

    Arguments:
        task: Which task the user is making progress on.
        config: Where the config file is stored.
    """
    cfg = Config.from_path(config)

    try:
        task_obj = Task.load(cfg, task)
    except TaskNotFoundError as e:
        print(f"Error: Task '{e.task}' not found", file=sys.stderr)
        if e.matches:
            print("\nDid you mean one of these?", file=sys.stderr)
            for match in e.matches:
                print(f"  {match}", file=sys.stderr)
        sys.exit(1)

    # Calculate total completed
    total = sum(count for _, count in task_obj.data)

    # Calculate progress metrics
    now = datetime.now(tz=datetime.timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=datetime.timezone.utc)
    year_end = datetime(now.year, 12, 31, tzinfo=datetime.timezone.utc)

    days_elapsed = (now - year_start).days
    days_remaining = (year_end - now).days + 1  # Include today
    days_in_year = (year_end - year_start).days + 1

    expected = int((days_elapsed / days_in_year) * 10000)
    daily_needed = (
        (10000 - total) / days_remaining if days_remaining > 0 else float("inf")
    )

    # Display results
    print(f"Progress for {task}:")
    print(f"Completed: {total:,} / 10,000 ({(total / 10000) * 100:.1f}%)")
    print(f"Expected:  {expected:,} by today")
    if total < expected:
        print(f"Behind by: {expected - total:,}")
    else:
        print(f"Ahead by:  {total - expected:,} ")
    print("\nTo reach 10,000 by year end:")
    print(f"Need {daily_needed:.0f} per day for {days_remaining} days")


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
            lock_file.unlink()  # Delete the lock file


if __name__ == "__main__":
    tyro.extras.subcommand_cli_from_dict({
        "add": add,
        "progress": progress,
    })
