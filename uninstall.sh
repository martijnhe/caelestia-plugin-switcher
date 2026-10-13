#!/bin/bash
# Removes the switcher's marked edits and the placement service. Other widgets' edits are kept.
set -euo pipefail
src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
conf=${XDG_CONFIG_HOME:-$HOME/.config}
target=$conf/quickshell/caelestia
python3 "$src/patch.py" revert "$target"
rm -f -- "$target/services/PluginState.qml"
echo "Removed. Restart the shell."
