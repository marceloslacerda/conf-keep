import settings
import sys
import confkeep_commands

VERSION = '0.1'
help_txt = f"""#{settings.SERVICE_NAME}

A multi-host, multi-path etckeeper alternative.

{settings.SERVICE_NAME} allows you to continuously keep track of changes to your configuration files
wherever they are across multiple hosts. It uses cron to periodically synchronize a copy of the configuration
you want to monitor and commits the changes to a single repository. Each host will have its own branch on the git
repository.

You can use by following 4 simple steps.

Step 1 `{settings.SERVICE_NAME} {settings.BOOTSTRAP_COMMAND}`
This will configure the repository you want to use for tracking the changes. 
2. `{settings.SERVICE_NAME} {settings.ADD_HOST_COMMAND}`
This command will add the current host to the repository.
3. `{settings.SERVICE_NAME} {settings.ADD_WATCH_COMMAND}`
This is how you specify which file/directory you want to monitor for changes
4. `{settings.SERVICE_NAME} {settings.INSTALL_CRON_COMMAND}` 
This is a helper command that you can use to automatically install an entry to your crontab that will call the
synchronization command.

(Optional) 5. `{settings.SERVICE_NAME} {settings.SYNC_COMMAND}`
This is the command that `{settings.INSTALL_CRON_COMMAND}` calls. You normally don't run this manually.

Each command (except for `{settings.SYNC_COMMAND}`) is interactive and will guide you through the configuration process.
If you want to run the command non-interactively check confkeep/settings.py to know all the possible environment
variables you can pass.
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(help_txt)
        exit(1)
    command = sys.argv[1]
    if command in ("-h", "--help"):
        print(help_txt)
    if command in ("-v", "--version"):
        print(VERSION)
    if command == settings.BOOTSTRAP_COMMAND:
        confkeep_commands.bootstrap_repository()
    elif command == settings.ADD_HOST_COMMAND:
        confkeep_commands.config_host()
    elif command == settings.ADD_WATCH_COMMAND:
        confkeep_commands.track_dir()
    elif command == settings.INSTALL_CRON_COMMAND:
        confkeep_commands.install_cron()
    elif command == settings.SYNC_COMMAND:
        confkeep_commands.watchdog()
    exit(0)
