# Ten Thousand

A simple CLI tool to track progress towards completing 10,000 repetitions of various activities over the course of a year.

## Installation

1. Clone this repository
2. Make the script executable:
   ```bash
   chmod +x main.py
   ```
3. Create a symlink in your PATH (optional):
   ```bash
   ln -s /path/to/tenthousand/main.py ~/.local/bin/10k
   ```

## Usage

Add progress to a task:
```bash
10k add 5 pushups      # Add 5 pushups to today's count
10k add 30 meditation  # Add 30 minutes of meditation
```

Check progress on a task:
```bash
10k progress pushups    # See progress towards 10k pushups
10k progress meditation # See progress towards 10k minutes
```

The tool will:
- Track multiple tasks separately
- Show your current progress
- Compare against expected progress for this point in the year
- Calculate how many repetitions per day you need to reach 10k by year end

## Configuration

By default, the tool stores its config in `~/.config/tenthousand/config.toml` and data in `~/.local/state/tenthousand/`.

You can specify a different config file with the `--config` flag:
```bash
10k add 5 pushups --config path/to/config.toml
```
