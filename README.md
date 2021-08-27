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

**conf-keep** supports python ≥ `3.6`.

## Usage

You can use by following 4 simple steps.

1. `python3 -m confkeep bootstrap`

   This will configure the repository you want to use for tracking the changes. 
2. `python3 -m confkeep add-host`

   This command will add the current host to the repository.
3. `python3 -m confkeep watch`
   
   This is how you specify which file/directory you want to monitor for changes
4. `python3 -m confkeep install-cron`

   This is a helper command that you can use to automatically install an entry to your crontab that will call the
synchronization command.

5. (Optional) `python3 -m confkeep sync`

   This is the command that the *cronfile* calls. You normally don't run this manually.

Each command (except for `sync`) is interactive and will guide you through the configuration process.
If you want to run the command *non-interactively* check [confkeep/settings.py](confkeep/settings.py) to know all the possible environment
variables you can pass.

## Running as a regular user

If you want to run **conf-keep** with a non-root user you should make sure to have followed some or all of the following
steps:
1. Create a user account for it
2. Give it permissions for the directories that it will be using.
3. Configure its git credentials.
4. Set the`CK_USER` environment variable correctly.

Here's an example:

```bash
sudo useradd -m -s /bin/bash conf-keep
sudo touch /usr/local/bin/conf-keep-sync /etc/cron.d/conf-keep
sudo chown conf-keep /var/backups/local-repo-dir /usr/local/bin/conf-keep-sync /etc/cron.d/conf-keep
sudo su conf-keep
git config --global user.email "user@test.com"
git config --global user.name "User Name"
# This last step assumes that you will add a public ssh key to your git host. Adjust it to your necessities.
ssh-keygen
cat ~/.ssh/id_rsa.pub
# Follow the instructions this README.md Usage section.
```
