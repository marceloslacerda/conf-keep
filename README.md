# conf-keep

A multi-host, multi-path [etckeeper](https://etckeeper.branchable.com/) alternative.

**conf-keep** allows you to continuously keep track of changes to your configuration files
wherever they are across multiple hosts. It uses cron to periodically synchronize a copy of the configuration
you want to monitor and commits the changes to a single repository. Each host will have its own branch on the git
repository.

## Installation

```bash
git clone https://github.com/marceloslacerda/conf-keep
cd conf-keep
# That's all! You can run conf-keep with
python -m confkeep --help
```

## Usage

You can use by following 4 simple steps.

1. `conf-keep bootstrap`

   This will configure the repository you want to use for tracking the changes. 
2. `conf-keep add-host`

   This command will add the current host to the repository.
3. `conf-keep watch`
   
   This is how you specify which file/directory you want to monitor for changes
4. `conf-keep install-cron`

   This is a helper command that you can use to automatically install an entry to your crontab that will call the
synchronization command.

5. (Optional) `conf-keep sync`

   This is the command that the *cronfile* calls. You normally don't run this manually.

Each command (except for `sync`) is interactive and will guide you through the configuration process.
If you want to run the command *non-interactively* check [confkeep/settings.py](confkeep/settings.py) to know all the possible environment
variables you can pass.
