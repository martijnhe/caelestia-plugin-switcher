# Caelestia plugin switcher

Lets each caelestia-* widget choose where it shows, from **Nexus → Dashboard → Plugin switches**:

- **Off**: hidden everywhere
- **Right bar**: the icon in the plugin group above the clock (default)
- **Top bar**: a tab in the dashboard's top strip, next to LocalSend and Notes

It also turns the **Dashboard**, **Media**, **Weather** and **Performance** tabs on and off from the same page.

Choices are saved to `~/.config/caelestia/plugin-toggles.json`. The switcher covers tailscale, webcam,
screens, sony and syncthing (edit the `plugins` list in `services/PluginState.qml` to add more).

## What it changes

- `bar/components/PluginIcons.qml`: a plugin shows in the right bar only when its placement is "right"; the group hides when none are
- `dashboard/Tabs.qml`: a dashboard tab can show an image icon (used for the Tailscale and Syncthing logos)
- `dashboard/Content.qml`: the five plugin tabs (shown when placed on top) and their panes, 840×480
- `nexus/pages/panels/DashboardPanel.qml`: the Plugin switches section and the Dashboard / Media / Weather / Performance buttons

## Files

| File | Purpose |
| --- | --- |
| `files/services/PluginState.qml` | Singleton: reads and saves each plugin's placement |
| `files/snippets/` | Text of the tab entries and components, placement items and Plugin switches block |
| `patch.py` | Applies or reverts the edits in the four shared files |
| `install.sh` | Copies the singleton and applies the edits |
| `uninstall.sh` | Reverts the edits and removes the singleton |

Each inserted line ends with `// plugin:switcher`, and each block is wrapped in
`// >>> plugin:switcher <tag>` markers. The replaced line keeps its original in a `was:` comment.
So `uninstall.sh` removes exactly these edits and leaves the other widgets' edits alone.
Re-running `install.sh` is safe: anything already in place is skipped.

## Install

Install a caelestia-* widget first (it creates the shared plugin group). Then:

```bash
./install.sh
kill $(pgrep -x qs); qs -c caelestia -n -d
```

## Uninstall

```bash
./uninstall.sh
```
