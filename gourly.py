#!/usr/bin/env python3
"""
Setup an hourly cron job to auto-commit and push from the current directory.
Run this script once inside the Git repository you want to keep auto-updated.
"""

import os
import subprocess
import sys
import tempfile

def get_script_dir():
    """Return the absolute path of the directory containing this script."""
    return os.path.dirname(os.path.abspath(__file__))

def get_current_crontab(user=False):
    """Retrieve current user's crontab as a list of lines."""
    try:
        if user:
            cmd = ['crontab', '-l']
        else:
            cmd = ['crontab', '-l']
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            # No crontab for user
            return []
    except Exception as e:
        print(f"Error reading crontab: {e}")
        return []

def write_crontab(lines, user=False):
    """Write the given lines as the user's crontab."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('\n'.join(lines) + '\n')
        tmpname = tmp.name
    try:
        subprocess.run(['crontab', tmpname], check=True)
        os.unlink(tmpname)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install crontab: {e}")
        sys.exit(1)

def cron_entry_exists(entries, job_pattern):
    """Check if any entry contains the job_pattern."""
    for line in entries:
        if job_pattern in line and not line.strip().startswith('#'):
            return True
    return False

def ensure_cron_running():
    """Check if cron service is running; if not, try to start it."""
    try:
        # Check if cron is running (common on WSL)
        result = subprocess.run(['pgrep', 'cron'], capture_output=True)
        if result.returncode != 0:
            print("Cron service is not running. Attempting to start...")
            subprocess.run(['sudo', 'service', 'cron', 'start'], check=True)
            print("Cron started.")
    except Exception as e:
        print(f"Warning: Could not verify/start cron: {e}")
        print("You may need to start cron manually with: sudo service cron start")

def main():
    repo_dir = get_script_dir()
    print(f"Setting up hourly auto-commit for: {repo_dir}")

    # Verify this is a git repository
    if not os.path.isdir(os.path.join(repo_dir, '.git')):
        print("Error: No .git directory found. Please run this script from the root of a Git repository.")
        sys.exit(1)

    # The command that will be run every hour
    # Use full paths to git if needed, but usually PATH is set
    job_cmd = f'cd {repo_dir} && git add . && git commit -m "autoupdate" && git push'
    # Cron schedule: every hour at minute 0
    cron_schedule = '0 * * * *'
    full_job = f'{cron_schedule} {job_cmd} >/dev/null 2>&1'

    # Get existing crontab
    current = get_current_crontab()
    if cron_entry_exists(current, job_cmd):
        print("A cron job for this directory already exists. No changes made.")
    else:
        # Append new job
        new_crontab = current + [full_job]
        write_crontab(new_crontab)
        print("Cron job added successfully.")

    ensure_cron_running()

    print("\nHourly auto-commit is now active.")
    print("To view your crontab, run: crontab -l")
    print("To remove the job, edit your crontab with: crontab -e")

if __name__ == '__main__':
    main()