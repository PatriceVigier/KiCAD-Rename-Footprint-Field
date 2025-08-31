# -*- coding: utf-8 -*-
# KiCad 9 Action Plugin — Rename footprint field (rename only)
#
# This plugin renames a field/property across all footprints in the open PCB.
# Example: "PART NUMBER" → "MPN"
#
# Usage:
#   - Install this file into your KiCad user plugin folder
#   - In PCB Editor, go to Tools → External Plugins → Rename field…
#   - A dialog will let you type the old field name and the new one
#   - The plugin will update every footprint on the current board
#
# Author: Patrice Vigier (MIT License)

import pcbnew
import wx
import os

def _rename_fields_on_board(board, old_field, new_field):
    """
    Rename old_field -> new_field on all footprints in the given board.

    Supports two APIs, depending on how the field is stored:
      A) Properties (GetProperties / SetProperty / ClearProperty)
      B) Fields (GetFields / SetName / GetText)

    Returns:
      count_modified: number of footprints actually changed
      count_found: total number of footprints where the old_field was found
    """
    old_l = (old_field or "").strip().lower()  # normalized lowercase match
    count_modified = 0
    count_found = 0

    # Iterate through every footprint on the board
    for fp in board.GetFootprints():

        # ---------- CASE A: Property dictionary ----------
        try:
            props = fp.GetProperties()  # Some builds may not support this
            match_key = None
            for k in list(props.keys()):
                if (k or "").strip().lower() == old_l:
                    match_key = k
                    break

            if match_key is not None:
                # Found a match
                count_found += 1
                value = props[match_key]

                # Create or overwrite the new property
                try:
                    fp.SetProperty(new_field, value)
                except AttributeError:
                    # Fallback if SetProperty is missing
                    props[new_field] = value

                # Remove the old property
                try:
                    fp.ClearProperty(match_key)
                except Exception:
                    try:
                        del props[match_key]
                    except Exception:
                        pass

                count_modified += 1
                continue  # Done with this footprint, go to next
        except AttributeError:
            # This KiCad build does not expose GetProperties()
            pass

        # ---------- CASE B: Fields (textual named fields) ----------
        try:
            fields = fp.GetFields()  # Some builds may not support this either
        except AttributeError:
            fields = []

        renamed_here = False
        for fld in fields:
            # Compare field names in lowercase
            name = (getattr(fld, "GetName", lambda: "")() or "").strip().lower()
            if name == old_l:
                count_found += 1
                try:
                    # Try to rename directly in place
                    fld.SetName(new_field)
                except Exception:
                    # Fallback: create a new property instead (so value is preserved)
                    try:
                        value = (getattr(fld, "GetText", lambda: "")() or "")
                        fp.SetProperty(new_field, value)
                    except Exception:
                        pass
                count_modified += 1
                renamed_here = True
                break

        if renamed_here:
            continue

    # Refresh PCB editor so changes are visible immediately
    pcbnew.Refresh()
    return count_modified, count_found


class _RenameDialog(wx.Dialog):
    """Simple dialog box asking for old/new field names."""

    def __init__(self, parent, default_old="OLDname", default_new="NEWname"):
        super().__init__(parent, title="Rename footprint field",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetSize(wx.Size(420, 170))

        s = wx.BoxSizer(wx.VERTICAL)

        # Old field name input
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(wx.StaticText(self, label="Old field name:"), 0,
                 wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.txt_old = wx.TextCtrl(self, value=default_old)
        row1.Add(self.txt_old, 1, wx.EXPAND)
        s.Add(row1, 0, wx.ALL | wx.EXPAND, 8)

        # New field name input
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(wx.StaticText(self, label="New field name:"), 0,
                 wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.txt_new = wx.TextCtrl(self, value=default_new)
        row2.Add(self.txt_new, 1, wx.EXPAND)
        s.Add(row2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        # OK/Cancel buttons
        btns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        s.Add(btns, 0, wx.ALL | wx.EXPAND, 8)

        self.SetSizerAndFit(s)

    def get_values(self):
        """Return tuple (old_field, new_field) from dialog."""
        return (self.txt_old.GetValue().strip(),
                self.txt_new.GetValue().strip())


class RenameFieldPlugin(pcbnew.ActionPlugin):
    """KiCad Action Plugin wrapper for the rename function."""

    def defaults(self):
        self.name = "Rename field… (rename only)"
        self.category = "Modify footprints"
        self.description = "Rename a footprint field/property across all footprints on the open PCB."
        # Show button in External Plugins toolbar
        try:
            self.show_toolbar_button = True
        except Exception:
            pass
        # Optional icon (must exist as PNG in same folder)
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "v_rename.png")

    def Run(self):
        board = pcbnew.GetBoard()
        dlg = _RenameDialog(None, "OLDname", "NEWname")

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        old_field, new_field = dlg.get_values()
        dlg.Destroy()

        # Basic checks
        if not old_field or not new_field:
            wx.MessageBox("Please fill both field names.",
                          "Rename field", wx.ICON_WARNING)
            return
        if old_field.strip().lower() == new_field.strip().lower():
            wx.MessageBox("Old and new field names are identical.",
                          "Rename field", wx.ICON_WARNING)
            return

        # Perform the renaming
        modified, found = _rename_fields_on_board(board, old_field, new_field)

        # Show summary
        wx.MessageBox(
            f"Renamed {found} occurrence(s) of '{old_field}' → '{new_field}'.\n"
            f"Modified footprints: {modified}.",
            "Rename field", wx.ICON_INFORMATION
        )

# Register the plugin with KiCad
RenameFieldPlugin().register()
