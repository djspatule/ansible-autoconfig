#!/bin/sh
set -eu
# Local-only linting. No CI service, no cloud cost: this just runs yamllint and
# ansible-lint against the repo on your own machine.
#
# On first run it builds a throwaway Python virtualenv (.lint-venv, gitignored)
# so the linters do not have to be installed system-wide. Delete that folder any
# time to force a clean reinstall.
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
venv_dir="$repo_dir/.lint-venv"

if [ ! -x "$venv_dir/bin/ansible-lint" ]; then
  echo "== setting up local lint virtualenv (first run only) =="
  python3 -m venv "$venv_dir"
  "$venv_dir/bin/pip" install --quiet --upgrade pip
  "$venv_dir/bin/pip" install --quiet yamllint ansible-lint
fi

cd "$repo_dir"

echo "== yamllint =="
"$venv_dir/bin/yamllint" .

echo "== ansible-lint =="
"$venv_dir/bin/ansible-lint"

echo "== lint OK =="
