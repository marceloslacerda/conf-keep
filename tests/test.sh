#!/bin/sh -e
dir="$(dirname $0)/.."
cd "$dir"
rm -rf repo-*
mkdir repo-origin
cd repo-origin
git init --bare
cd ..
export ASSUME_YES=TRUE
export IGNORE_SYNC_ERRORS=TRUE
export REPO_PATH="$dir/repo-path"
export REMOTE="$dir/repo-origin"
export MONITORED_PATH="/etc"
python -m confkeep bootstrap
python -m confkeep add-host
python -m confkeep watch
python -m confkeep sync
python -m confkeep install-cron
cat /etc/cron.d/conf-keep
echo > /etc/cron.d/conf-keep
