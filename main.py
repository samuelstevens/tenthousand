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
from datetime import datetime, timezone
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
def get_task(task: str, cfg: Config) -> pathlib.Path:
    """
    Get the task file path and verify it exists, suggesting alternatives if not found.

    Arguments:
        task: Which task to look for.
        cfg: The configuration object.

    Returns:
        The path to the task file.

    Exits with error if task doesn't exist and user doesn't want to create it.
    """
    task_file = cfg.root / f"{task}.csv"
    
    # Get list of existing tasks
    existing_tasks = [f.stem for f in cfg.root.glob("*.csv")]
    
    if not task_file.exists():
        if existing_tasks:
            # Find similar task names
            matches = difflib.get_close_matches(task, existing_tasks, n=3, cutoff=0.6)
            
            print(f"Error: Task '{task}' not found", file=sys.stderr)
            if matches:
                print("\nDid you mean one of these?", file=sys.stderr)
                for match in matches:
                    print(f"  {match}", file=sys.stderr)
            sys.exit(1)
        else:
            # No tasks exist yet, create the first one
            task_file.parent.mkdir(parents=True, exist_ok=True)
            with locked(task_file, "w") as fd:
                writer = csv.writer(fd)
                writer.writerow(["timestamp", "count"])
            print(f"Created new task file for '{task}'")
    
    return task_file


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

    task_file = get_task(task, cfg)
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
        timestamp = datetime.now(tz=timezone.utc).isoformat()
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
    task_file = get_task(task, cfg)

    # Calculate total completed
    total = 0
    with open(task_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += int(row["count"])

    # Calculate progress metrics
    now = datetime.now(tz=timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(now.year, 12, 31, tzinfo=timezone.utc)

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
