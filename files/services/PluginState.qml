pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

// Where each caelestia-* plugin shows: "off", "right" (plugin group above the clock)
// or "top" (a tab in the dashboard's top strip). Saved to ~/.config/caelestia/plugin-toggles.json.
Singleton {
    id: root

    readonly property var plugins: ["tailscale", "webcam", "screens", "sony", "syncthing"]

    function placementOf(name: string): string {
        return (settingsAdapter.placement ?? {})[name] ?? "right";
    }

    function setPlacement(name: string, place: string): void {
        const next = Object.assign({}, settingsAdapter.placement ?? {});
        next[name] = place;
        settingsAdapter.placement = next;
    }

    function anyIn(place: string): bool {
        return root.plugins.some(n => placementOf(n) === place);
    }

    FileView {
        path: `${Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config"}/caelestia/plugin-toggles.json`
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onAdapterUpdated: writeAdapter()
        onLoadFailed: err => {
            if (err === FileViewError.FileNotFound)
                writeAdapter();
        }

        JsonAdapter {
            id: settingsAdapter

            property var placement: ({})
        }
    }
}
