# Rename Footprint Field (KiCad 9 Action Plugin, with dialog)

This KiCad Action Plugin renames (or copies) a custom field on **all footprints** in the **currently opened PCB**.
A dialog lets you enter:

* **Old field name** (to find)
* **New field name** (to create/rename to)
* **Copy instead of rename** (keep old field)

It works with boards whose footprints expose either:

* the **Properties API** (`GetProperties/SetProperty/ClearProperty`), or
* the **Fields API** (`GetFields/SetName/GetText`).

> Tested on KiCad 9 / Windows 11.

---

## What it does

For each footprint on the open board:

1. If a field named like the **Old field name** exists (case-insensitive match):

   * If **Copy instead of rename** is checked: creates/overwrites **New field name** with the same value and **keeps** the old field.
   * Otherwise: **renames** it to **New field name** (or creates the new property then removes the old, depending on which API is available).
2. Refreshes the PCB view when done.
3. Shows a summary: occurrences found and footprints modified.

> Matching is **case-insensitive** for the *old* name; the *new* name is created exactly as you type it.

---

## Installation

1. Save the plugin file as, e.g., `rename_field_plugin.py`.
2. Place it in your KiCad user plugins folder (create folders if needed):

* **Windows**

  * Preferred (KiCad 9):
    `%APPDATA%\kicad\9.0\scripting\plugins\`
  * Or use your custom `KICAD_USER_SCRIPTS` path:
    `KICAD_USER_SCRIPTS\scripting\plugins\`
* **macOS**
  `~/Library/Preferences/kicad/9.0/scripting/plugins/`
* **Linux**
  `~/.local/share/kicad/9.0/scripting/plugins/`

3. (Optional) Put a `.png` icon in the script folder and set `self.icon_file_name` line 147`.
For example         self.icon_file_name = "myIcone.png"  # put a .png next to it if you want an icon
Size 24x24 pixels

4. Restart KiCad (or at least restart PCB Editor) so the plugin is discovered.

---

## Usage

1. Open your `.kicad_pcb` in **PCB Editor**.
2. Go to **Tools → External Plugins → Rename field….
3. In the dialog:

   * **Old field name** (e.g. `PART NUMBER`)
   * **New field name** (e.g. `MPN`)
   * **Copy instead of rename** (check to keep the old field too)
4. Click **OK**.
   A message box will summarize what was found and modified.

---

## Safety & Undo
* **Recommended:** save a copy, use Git, or duplicate your board file before running.

---

## Troubleshooting

**The plugin doesn’t show up in the menu**

* Verify the file is under a `…/scripting/plugins/` folder listed above.
* Restart KiCad.
* Open **Tools → Scripting Console** to see import errors (e.g., indentation, missing `wx`).

**“0 modified” but fields exist**

* The **Old field name** must match the existing name (comparison is case-insensitive, but spacing and punctuation matter).
* Some footprints may expose data only via the Fields API; this plugin tries both APIs.

**I want a toolbar button**

* In `defaults()` the code sets `self.show_toolbar_button = True` (if supported).
  Provide an icon via `self.icon_file_name = "your_icon.png"`.

---


---

If you want, I can now write the **separate README** for the *schematic field re-ordering* script (single-file only, as you requested), also in English and GitHub-ready.
