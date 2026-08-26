#!/bin/bash
##
## Copyright (c) 2020-2024 Key4hep-Project.
##
## This file is part of Key4hep.
## See https://key4hep.github.io/key4hep-doc/ for further info.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##

# This script has to be sourced: executing it would set up a shell that exits
# immediately afterwards.
if ! (return 0 2>/dev/null); then
    echo "This script must be sourced:  source setup.sh"
    exit 1
fi

_TUTORIAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_TUTORIAL_PREV_DIR="${PWD}"

# 1. key4hep stack, pinned so that everybody follows the tutorial on the same
#    software. Reuse it only when the requested release is already active.
KEY4HEP_VERSION="${KEY4HEP_VERSION:-2026-04-08}"
_TUTORIAL_NEED_STACK=true
case "${KEY4HEP_STACK:-}" in
  */releases/"${KEY4HEP_VERSION}"/*)
    if command -v k4run > /dev/null 2>&1; then
        echo "key4hep ${KEY4HEP_VERSION} already set up, skipping"
        _TUTORIAL_NEED_STACK=false
    else
        # KEY4HEP_STACK is exported but the paths it describes are not in this
        # shell. That happens whenever a process inherits the variable without
        # the environment, for instance a terminal opened by a VS Code server
        # that was itself started from a key4hep shell. The stack refuses to set
        # itself up again while the variable is there, so clear it first.
        echo "key4hep ${KEY4HEP_VERSION} is recorded but not active here, setting it up again ..."
        unset KEY4HEP_STACK
    fi
    ;;
  "")
    echo "Setting up key4hep ${KEY4HEP_VERSION} ..."
    ;;
  *)
    echo "A different key4hep release is already active: ${KEY4HEP_STACK}"
    echo "Start a fresh shell without it, then source setup.sh again."
    return 1
    ;;
esac

if ${_TUTORIAL_NEED_STACK}; then
    if ! source /cvmfs/sw.hsf.org/key4hep/setup.sh -r "${KEY4HEP_VERSION}"; then
        echo "Failed to set up key4hep ${KEY4HEP_VERSION}."
        return 1
    fi
fi

# The stack prints rather than fails in a few situations, so confirm that its
# tools are really reachable before building anything on top of it.
if ! command -v k4run > /dev/null 2>&1; then
    echo "key4hep ${KEY4HEP_VERSION} did not set up correctly: k4run is not on PATH."
    echo "Start a fresh shell and source setup.sh again."
    return 1
fi

# 2. Make the libraries built in this repository visible.
cd "${_TUTORIAL_ROOT}" || return 1
k4_local_repo
cd "${_TUTORIAL_PREV_DIR}" || return 1

# 3. A virtual environment that inherits everything from the stack. Repair an
#    incomplete environment too; VS Code can otherwise leave behind an empty
#    .venv after a failed attempt to install notebook dependencies.
if [ ! -x "${_TUTORIAL_ROOT}/.venv/bin/python3" ] || \
   [ ! -f "${_TUTORIAL_ROOT}/.venv/bin/activate" ] || \
   ! grep -q '^include-system-site-packages = true$' \
       "${_TUTORIAL_ROOT}/.venv/pyvenv.cfg" 2>/dev/null; then
    if [ -d "${_TUTORIAL_ROOT}/.venv" ]; then
        echo "Repairing incomplete .venv ..."
    else
        echo "Creating .venv ..."
    fi
    python -m venv --clear "${_TUTORIAL_ROOT}/.venv" \
        --system-site-packages --prompt "DRDCalo Tutorial"
fi

source "${_TUTORIAL_ROOT}/.venv/bin/activate"

# venv activation scripts contain the absolute path used when they were
# created. Normalise it here so that a moved checkout (or a checkout created
# through a mounted workspace) still selects this repository's interpreter.
export VIRTUAL_ENV="${_TUTORIAL_ROOT}/.venv"

# Move the environment to the front unconditionally rather than only adding it
# when absent: step 1 prepends the stack's own bin directories, so on a second
# `source setup.sh` in the same shell the stack python would otherwise sit ahead
# of this one and the rest of this script would configure the wrong interpreter.
_TUTORIAL_PATH=""
_TUTORIAL_IFS="${IFS}"
IFS=':'
for _TUTORIAL_ENTRY in ${PATH}; do
    [ "${_TUTORIAL_ENTRY}" = "${VIRTUAL_ENV}/bin" ] && continue
    _TUTORIAL_PATH="${_TUTORIAL_PATH:+${_TUTORIAL_PATH}:}${_TUTORIAL_ENTRY}"
done
IFS="${_TUTORIAL_IFS}"
export PATH="${VIRTUAL_ENV}/bin${_TUTORIAL_PATH:+:${_TUTORIAL_PATH}}"
unset _TUTORIAL_PATH _TUTORIAL_IFS _TUTORIAL_ENTRY
hash -r 2>/dev/null

# 4. Make the drdcalo_tutorials module importable. Every exercise resolves its
#    input and output files through it, so it has to be on PYTHONPATH before
#    the environment is captured below.
case ":${PYTHONPATH:-}:" in
  *":${_TUTORIAL_ROOT}/python:"*) ;;
  *) export PYTHONPATH="${_TUTORIAL_ROOT}/python${PYTHONPATH:+:${PYTHONPATH}}" ;;
esac

#    A .pth file in the virtual environment makes the module importable by
#    .venv/bin/python whatever PYTHONPATH it is started with. Jupyter kernels
#    launched by an editor do not reliably inherit the variable above, and a
#    kernel already running when this script runs keeps its old environment.
#
#    The file works out the location itself rather than storing it: .venv lives
#    inside the repository, so the parent of sys.prefix is the repository root.
#    A stored absolute path would be wrong for everybody else the moment this
#    script runs against a different mount point, such as inside a container.
if ! python - <<'PYEOF'
import pathlib
import sys
import sysconfig

prefix = pathlib.Path(sys.prefix)
if not (prefix / "pyvenv.cfg").exists():
    # Refuse to write anywhere but the tutorial's own environment. Without this
    # check a mis-ordered PATH would send the file into the read-only stack.
    raise SystemExit(f"{sys.executable} is not the tutorial virtual environment")

site_packages = pathlib.Path(sysconfig.get_paths()["purelib"])
site_packages.mkdir(parents=True, exist_ok=True)
(site_packages / "drdcalo-tutorials.pth").write_text(
    "import os, site, sys;"
    " site.addsitedir(os.path.join(os.path.dirname(sys.prefix), 'python'))\n"
)
PYEOF
then
    echo "Warning: could not register drdcalo_tutorials inside .venv."
    echo "  It stays importable in this shell through PYTHONPATH, but a Jupyter"
    echo "  kernel started by an editor may not find it. Delete .venv and source"
    echo "  setup.sh again to rebuild the environment."
fi

# Step 5 records absolute paths for an editor running on the host. Inside a
# container the repository is mounted somewhere else, so writing .env there
# would point VS Code at paths that do not exist on the host and the notebooks
# would stop working. Everything above applies either way.
_TUTORIAL_IN_CONTAINER=false
if [ -n "${APPTAINER_CONTAINER:-}${SINGULARITY_CONTAINER:-}" ] || \
   [ -n "${APPTAINER_NAME:-}${SINGULARITY_NAME:-}" ] || \
   [ -f /.dockerenv ]; then
    _TUTORIAL_IN_CONTAINER=true
fi

if ${_TUTORIAL_IN_CONTAINER}; then
    echo
    echo "Container detected: skipping .env."
    echo "  It is read on the host, and would record ${_TUTORIAL_ROOT},"
    echo "  which is this container's mount point. Source setup.sh on the host"
    echo "  to set it up for notebooks opened there."
    echo
    echo "Environment ready (container)."
    echo "  python : $(command -v python)"
    export DRDCALO_TUTORIALS_ROOT="${_TUTORIAL_ROOT}"
    unset _TUTORIAL_ROOT _TUTORIAL_PREV_DIR _TUTORIAL_IN_CONTAINER _TUTORIAL_NEED_STACK
    return 0
fi

# 5. Capture the environment so that Jupyter kernels started by an editor, which
#    do not inherit this shell, still find ROOT, DD4hep and podio. The repository
#    location is exported too, so that notebooks can locate their input file
#    whatever directory the editor happens to start them in.
export DRDCALO_TUTORIALS_ROOT="${_TUTORIAL_ROOT}"
python - > "${_TUTORIAL_ROOT}/.env" <<'PYEOF'
import os

# PKG_CONFIG_PATH is long and unnecessary, and an over-long environment makes
# process startup fail. The container variables are dropped because they confuse
# editors running outside the container.
SKIP = {"PKG_CONFIG_PATH", "_", "SHLVL", "OLDPWD", "PWD"}

for name, value in sorted(os.environ.items()):
    if name in SKIP or name.startswith("BASH_FUNC_"):
        continue
    if "SINGULARITY" in name or "APPTAINER" in name:
        continue
    if "\n" in value:          # cannot be represented in a .env file
        continue
    print(f'{name}="{value}"')
PYEOF

echo
echo "Environment ready."
echo "  python : $(command -v python)"
echo "  .env   : ${_TUTORIAL_ROOT}/.env ($(wc -l < "${_TUTORIAL_ROOT}/.env") variables)"
echo
echo "In VS Code, open ${_TUTORIAL_ROOT} as the workspace folder and select"
echo "the .venv interpreter. VS Code applies .env from the workspace folder,"
echo "which is what puts the key4hep runtime into the notebook."

unset _TUTORIAL_ROOT _TUTORIAL_PREV_DIR _TUTORIAL_IN_CONTAINER _TUTORIAL_NEED_STACK
