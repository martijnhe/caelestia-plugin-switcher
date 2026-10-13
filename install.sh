#!/bin/bash
# Installs the plugin switcher into the user copy of the Caelestia shell config:
# the placement service plus the marked edits in PluginIcons, Tabs, Content and DashboardPanel.
# Safe to re-run: edits that are already in place are left alone.
# Needs a caelestia-* widget installed first (it creates the shared plugin group in PluginIcons.qml).
set -euo pipefail

src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
conf=${XDG_CONFIG_HOME:-$HOME/.config}
target=$conf/quickshell/caelestia

[[ -d $target ]] || { echo "No user copy of the Caelestia shell at $target. Install a caelestia-* widget first." >&2; exit 1; }

cp -- "$src/files/services/PluginState.qml" "$target/services/PluginState.qml"
python3 "$src/patch.py" apply "$target"

echo "Installed. Restart the shell: kill \$(pgrep -x qs); qs -c caelestia -n -d"
