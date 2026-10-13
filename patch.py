#!/usr/bin/env python3
"""Add or remove the plugin switcher's edits in a user copy of the Caelestia shell config.

The switcher lets each caelestia-* plugin sit Off, in the right bar, or in the dashboard's
top strip, and turns the Dashboard/Media/Weather/Performance tabs on and off.

Every inserted line ends with `// plugin:switcher`, every multi-line block is wrapped in
`// >>> plugin:switcher <tag>` / `// <<< plugin:switcher <tag>`, and every replaced line keeps
the original in a `was:` comment, so the switcher can be reverted without touching the
edits of the other widgets.

usage: patch.py apply|revert CONFIG_DIR
"""
import base64
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNIP = HERE / "files" / "snippets"
MARK = "// plugin:switcher"
BLOCK_OPEN = "// >>> plugin:switcher"
BLOCK_CLOSE = "// <<< plugin:switcher"

PLUGIN_ICONS = "modules/bar/components/PluginIcons.qml"
TABS = "modules/dashboard/Tabs.qml"
CONTENT = "modules/dashboard/Content.qml"
PANEL = "modules/nexus/pages/panels/DashboardPanel.qml"

IMAGE_BLOCK = """\
            Image {
                id: tabImage

                visible: tab.hasImage
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: label.top
                width: icon.height
                height: icon.height

                source: tab.iconSource
                sourceSize: Qt.size(width * 2, height * 2)
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true

                layer.enabled: tab.iconTinted
                layer.effect: Colouriser {
                    sourceColor: "black"
                    colorizationColor: tab.current ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                }
            }
"""


def snip(name):
    return (SNIP / name).read_text().rstrip("\n").split("\n")


def find_one(lines, text):
    hits = [i for i, l in enumerate(lines) if l.rstrip() == text]
    if len(hits) != 1:
        raise SystemExit(f"anchor {text!r} found {len(hits)} times; the file differs from what this switcher expects")
    return hits[0]


def present(lines, key):
    """True when a line starting with `key` (or containing it, for blocks) is already in the file."""
    return any(l.strip().startswith(key) for l in lines)


def block(tag, body):
    return [f"{BLOCK_OPEN} {tag}"] + body + [f"{BLOCK_CLOSE} {tag}"]


def marked(lines):
    return [f"{l} {MARK}" if l.strip() else l for l in lines]


def edit(path, ops):
    """Apply ops to one file. Each op is skipped when its key is already present, so re-running is safe."""
    p = Path(path)
    lines = p.read_text().split("\n")
    changed = False
    for op in ops:
        kind = op[0]
        if kind == "replace":  # ("replace", old_line, new_line)
            _, old, new = op
            if present(lines, new.strip()):
                continue
            i = find_one(lines, old)
            lines[i] = f"{new} {MARK} was:{base64.b64encode(old.encode()).decode()}"
        elif kind in ("line_after", "line_before"):  # (kind, anchor, [new lines])
            _, anchor, new = op
            if all(present(lines, n.strip()) for n in new):
                continue
            i = find_one(lines, anchor)
            if kind == "line_after":
                lines[i + 1:i + 1] = marked(new)
            else:
                lines[i:i] = marked(new)
        elif kind == "block":  # ("block", where, anchor, tag, key, [body])
            _, where, anchor, tag, key, body = op
            if present(lines, key):
                continue
            if anchor is None:  # the page's final closing brace
                i = max(k for k, l in enumerate(lines) if l == "    }")
            elif where == "after_block_end":  # after the first "            }," following the anchor
                i = next(k for k in range(find_one(lines, anchor) + 1, len(lines)) if lines[k] == "            },") + 1
            else:
                i = find_one(lines, anchor)
                if where == "after":
                    i += 1
            lines[i:i] = block(tag, body)
        changed = True if changed else changed
        changed = True
    if changed:
        p.write_text("\n".join(lines))


def revert_file(path):
    p = Path(path)
    out = []
    skipping = None
    for l in p.read_text().split("\n"):
        s = l.strip()
        if skipping:
            if s == f"{BLOCK_CLOSE} {skipping}":
                skipping = None
            continue
        if s.startswith(f"{BLOCK_OPEN} "):
            skipping = s[len(BLOCK_OPEN) + 1:]
            continue
        if f"{MARK} was:" in l:
            original = base64.b64decode(l.split(f"{MARK} was:")[1].strip()).decode()
            out.append(original)
            continue
        if l.rstrip().endswith(MARK):
            continue
        out.append(l)
    p.write_text("\n".join(out))


def apply_all(root):
    root = Path(root)
    for rel in (PLUGIN_ICONS, TABS, CONTENT, PANEL):
        if not (root / rel).exists():
            raise SystemExit(f"{rel} missing in {root}; install a caelestia-* widget first")

    edit(root / PLUGIN_ICONS, [
        ("replace", "        visible: !(item?.hidden ?? false)",
         '        visible: PluginState.placementOf(name) === "right" && !(item?.hidden ?? false)'),
        ("line_after", "    readonly property alias items: iconColumn",
         ['    readonly property bool hidden: !PluginState.anyIn("right")']),
        ("line_after", "    clip: true", ['    visible: PluginState.anyIn("right")']),
    ])

    edit(root / TABS, [
        ("line_after", "import qs.components.controls", ["import qs.components.effects"]),
        ("line_after", "                iconName: modelData.iconName",
         ['                iconSource: modelData.iconSource ?? ""', "                iconTinted: modelData.iconTinted ?? true"]),
        ("line_after", "        required property string iconName",
         ['        property url iconSource: ""', "        property bool iconTinted: true",
          '        readonly property bool hasImage: iconSource.toString() !== ""']),
        ("line_before", "                text: tab.iconName", ["                visible: !tab.hasImage"]),
        ("block", "before", "            MaterialIcon {", "tab-image", "id: tabImage",
         IMAGE_BLOCK.rstrip("\n").split("\n") + [""]),
    ])

    edit(root / CONTENT, [
        ("block", "after_block_end", '                text: Tr.tr("LocalSend"),', "tab-entries",
         "component: tailscaleTabComponent,", snip("content-tab-entries.txt")),
        ("block", "before", "                id: performanceComponent", "tab-components",
         "id: tailscaleTabComponent", snip("content-tab-components.txt")),
    ])

    edit(root / PANEL, [
        ("block", "after", "    isSubPage: true", "placement-items", "readonly property list<MenuItem> placementItems",
         [""] + snip("dashboard-placement-items.txt")),
        ("block", "final", None, "plugin-switches", "// Plugin switches", snip("dashboard-plugin-switches.txt")),
    ])
    print("switcher edits applied (anything already in place was left alone)")


def revert_all(root):
    root = Path(root)
    for rel in (PLUGIN_ICONS, TABS, CONTENT, PANEL):
        if (root / rel).exists():
            revert_file(root / rel)
    print("switcher edits removed")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("apply", "revert"):
        raise SystemExit(__doc__)
    (apply_all if sys.argv[1] == "apply" else revert_all)(sys.argv[2])
