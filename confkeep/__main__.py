from . import settings
import sys
from . import confkeep_commands
from . import VERSION

help_txt = f"""# conf-keep

A multi-host, multi-path etckeeper alternative.

conf-keep allows you to continuously keep track of changes to your configuration files
wherever they are across multiple hosts. It uses cron to periodically synchronize a copy of the configuration
you want to monitor and commits the changes to a single repository. Each host will have its own branch on the git
repository.

You can use by following 4 simple steps.

Step 1 `conf-keep {confkeep_commands.BOOTSTRAP_COMMAND}`
This will configure the repository you want to use for tracking the changes. 
2. `conf-keep {confkeep_commands.ADD_HOST_COMMAND}`
This command will add the current host to the repository.
3. `conf-keep {confkeep_commands.ADD_WATCH_COMMAND}`
This is how you specify which file/directory you want to monitor for changes
4. `conf-keep {confkeep_commands.INSTALL_CRON_COMMAND}` 
This is a helper command that you can use to automatically install an entry to your crontab that will call the
synchronization command.

(Optional) 5. `conf-keep {confkeep_commands.SYNC_COMMAND}`
This is the command that `{confkeep_commands.INSTALL_CRON_COMMAND}` calls. You normally don't run this manually.

Each command (except for `{confkeep_commands.SYNC_COMMAND}`) is interactive and will guide you through the configuration process.
If you want to run the command non-interactively check confkeep/confkeep_commands.py to know all the possible environment
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
    ckwrapper = confkeep_commands.CKWrapper()
    try:
        if command == confkeep_commands.BOOTSTRAP_COMMAND:
            ckwrapper.bootstrap_repository()
        elif command == confkeep_commands.ADD_HOST_COMMAND:
            ckwrapper.config_host()
        elif command == confkeep_commands.ADD_WATCH_COMMAND:
            ckwrapper.track_dir()
        elif command == confkeep_commands.INSTALL_CRON_COMMAND:
            ckwrapper.install_cron()
        elif command == confkeep_commands.SYNC_COMMAND:
            ckwrapper.watchdog()
        else:
            print(f"Unknown command {command}\n")
            print(help_txt)
            exit(1)
    except confkeep_commands.ConfKeepError as error:
        if len(error.args) > 0:
            print(error.args[0])
        exit(1)
    except KeyboardInterrupt:
        print("Aborted by the user")
        exit(1)
    exit(0)
