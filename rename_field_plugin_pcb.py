#Rename field  in the PCB Foot Print
# -*- coding: utf-8 -*-
# Rename field plugin with dialog for KiCad 9
import pcbnew
import wx

def _rename_fields_on_board(board, old_field, new_field, copy_instead):
    """
    Renamee (or copy) old_field -> new_field on all foot print.
    Supported by two API :
      - A) Properties (GetProperties / SetProperty / HasProperty / ClearProperty)
      - B) Fields (GetFields / SetName / GetText)
    """
    old_l = (old_field or "").strip().lower()
    count_modified = 0
    count_found = 0

    for fp in board.GetFootprints():

        # ---------- CASE A: property dictionary ----------
        try:
            props = fp.GetProperties()  # may not exist depending on builds
            match_key = None
            for k in list(props.keys()):
                if (k or "").strip().lower() == old_l:
                    match_key = k
                    break

            if match_key is not None:
                count_found += 1
                value = props[match_key]
                # write/overwrite the new property
                try:
                    fp.SetProperty(new_field, value)
                except AttributeError:
                    # possible fallback if SetProperty does not exist
                    props[new_field] = value
                if not copy_instead:
                    try:
                        # some versions have ClearProperty/UnsetProperty
                        fp.ClearProperty(match_key)
                    except Exception:
                        del props[match_key]
                count_modified += 1
                continue  # we have processed by properties, move on to the next print
        except AttributeError:
            pass  # no GetProperties() on this build → try by Fields

        # ---------- CASE B: Fields (named text) ----------
        try:
            fields = fp.GetFields()  # list of named fields
        except AttributeError:
            fields = []

        done_here = False
        for fld in fields:
            name = (getattr(fld, "GetName", lambda: "")() or "").strip().lower()
            if name == old_l:
                count_found += 1
                value = (getattr(fld, "GetText", lambda: "")() or "")
                if copy_instead:
                    # duplicate: create a new field/property
                    try:
                        fp.SetProperty(new_field, value)   # preference: property
                    except Exception:
                        # otherwise, duplicate the field (if API available)
                        try:
                            fld2 = fld.Duplicate()          # not always present
                            fld2.SetName(new_field)
                            fp.Add(fld2)
                        except Exception:
                            pass
                else:
                    # rename: if possible, change the name of the field in place
                    try:
                        fld.SetName(new_field)
                    except Exception:
                        # fallback: create the new property then (if possible) delete the old one
                        try:
                            fp.SetProperty(new_field, value)
                        except Exception:
                            pass
                        # no safe API to remove the field on all builds → we leave it
                        pass
                count_modified += 1
                done_here = True
                break

        if done_here:
            continue

    pcbnew.Refresh()
    return count_modified, count_found



class _RenameDialog(wx.Dialog):
    def __init__(self, parent, default_old="PART NUMBER", default_new="MPN", default_copy=False):
        super().__init__(parent, title="Rename footprint field", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetSize(wx.Size(420, 200))

        s = wx.BoxSizer(wx.VERTICAL)

        # Old field
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(wx.StaticText(self, label="Old field name:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.txt_old = wx.TextCtrl(self, value=default_old)
        row1.Add(self.txt_old, 1, wx.EXPAND)
        s.Add(row1, 0, wx.ALL | wx.EXPAND, 8)

        # New field
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(wx.StaticText(self, label="New field name:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.txt_new = wx.TextCtrl(self, value=default_new)
        row2.Add(self.txt_new, 1, wx.EXPAND)
        s.Add(row2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        # Copy vs move
        self.chk_copy = wx.CheckBox(self, label="Copy instead of rename (keep old field)")
        self.chk_copy.SetValue(default_copy)
        s.Add(self.chk_copy, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Buttons
        btns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        s.Add(btns, 0, wx.ALL | wx.EXPAND, 8)

        self.SetSizerAndFit(s)

    def get_values(self):
        return (
            self.txt_old.GetValue().strip(),
            self.txt_new.GetValue().strip(),
            self.chk_copy.IsChecked(),
        )



class RenameFieldPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Rename field…"
        self.category = "Modify footprints"
        self.description = "Rename/duplicate a footprint field across all footprints on the open PCB."
        try:
            self.show_toolbar_button = True
        except Exception:
            pass
        self.icon_file_name = ""  # put a .png next to it if you want an icon

    def Run(self):
        board = pcbnew.GetBoard()

        # Default values ​​(change here if you want other default values)
        default_old = "Old Name"
        default_new = "New Name"
        default_copy = False

        # Dialog
        dlg = _RenameDialog(None, default_old, default_new, default_copy)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        old_field, new_field, copy_instead = dlg.get_values()
        dlg.Destroy()

        if not old_field or not new_field:
            wx.MessageBox("Please fill both field names.", "Rename field", wx.ICON_WARNING)
            return
        if old_field.strip().lower() == new_field.strip().lower():
            wx.MessageBox("Old and new field names are identical.", "Rename field", wx.ICON_WARNING)
            return

        modified, found = _rename_fields_on_board(board, old_field, new_field, copy_instead)

        # Summary
        verb = "copied" if copy_instead else "renamed"
        msg = (f"{verb.capitalize()} {found} occurrence(s) of '{old_field}' "
               f"→ '{new_field}'.\nModified footprints: {modified}.")
        wx.MessageBox(msg, "Rename field", wx.ICON_INFORMATION)

# Plugin Registration
RenameFieldPlugin().register()
