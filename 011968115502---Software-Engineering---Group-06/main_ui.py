"""Tkinter user interface for the Phone Book Management System."""

import tkinter as tk
from tkinter import messagebox, ttk

from add_contact import add_contact
from database import get_contact_by_id, init_database
from delete_contact import delete_contact as remove_contact
from edit_contact import edit_contact
from group_manager import (
    assign_contact_to_group,
    create_group,
    delete_group,
    get_groups,
    rename_group,
)
from search_contact import search_contacts
from view_contact import get_all_contacts

NO_GROUP_LABEL = "No group"


def _value_or_empty(value):
    return "" if value is None else value


class ContactFormDialog(tk.Toplevel):
    """Dialog used for both adding and editing contacts."""

    def __init__(self, parent, title, contact=None, on_saved=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.contact = contact
        self.on_saved = on_saved
        self.group_lookup = {}

        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.group_var = tk.StringVar(value=NO_GROUP_LABEL)

        self._build_form()
        self._load_groups()
        self._load_contact()

        self.transient(parent)
        self.grab_set()
        self.name_entry.focus_set()

    def _build_form(self):
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        labels = ["Name *", "Phone *", "Email", "Address", "Group"]
        for index, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(
                row=index, column=0, sticky="w", padx=(0, 10), pady=6
            )

        self.name_entry = ttk.Entry(frame, textvariable=self.name_var, width=36)
        self.phone_entry = ttk.Entry(frame, textvariable=self.phone_var, width=36)
        self.email_entry = ttk.Entry(frame, textvariable=self.email_var, width=36)
        self.address_entry = ttk.Entry(frame, textvariable=self.address_var, width=36)
        self.group_combo = ttk.Combobox(
            frame, textvariable=self.group_var, width=33, state="readonly"
        )

        widgets = [
            self.name_entry,
            self.phone_entry,
            self.email_entry,
            self.address_entry,
            self.group_combo,
        ]
        for index, widget in enumerate(widgets):
            widget.grid(row=index, column=1, sticky="ew", pady=6)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(labels), column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(button_frame, text="Save", command=self._save).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1
        )

    def _load_groups(self):
        group_options = [NO_GROUP_LABEL]
        self.group_lookup = {NO_GROUP_LABEL: None}
        for group in get_groups():
            label = f"{group['id']} - {group['name']}"
            group_options.append(label)
            self.group_lookup[label] = group["id"]
        self.group_combo["values"] = group_options

    def _load_contact(self):
        if not self.contact:
            return

        self.name_var.set(self.contact["name"])
        self.phone_var.set(self.contact["phone"])
        self.email_var.set(_value_or_empty(self.contact["email"]))
        self.address_var.set(_value_or_empty(self.contact["address"]))

        group_id = self.contact["group_id"]
        for label, value in self.group_lookup.items():
            if value == group_id:
                self.group_var.set(label)
                break

    def _selected_group_id(self):
        return self.group_lookup.get(self.group_var.get())

    def _save(self):
        try:
            if self.contact:
                edit_contact(
                    self.contact["id"],
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.email_var.get(),
                    self.address_var.get(),
                    self._selected_group_id(),
                )
                messagebox.showinfo(
                    "Contact Updated",
                    "Contact information was updated successfully.",
                    parent=self,
                )
            else:
                add_contact(
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.email_var.get(),
                    self.address_var.get(),
                    self._selected_group_id(),
                )
                messagebox.showinfo(
                    "Contact Added",
                    "New contact was added successfully.",
                    parent=self,
                )

            if self.on_saved:
                self.on_saved()
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Invalid Input", str(exc), parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not save contact.\n{exc}", parent=self)


class GroupManagerDialog(tk.Toplevel):
    """Dialog for creating, renaming, deleting, and assigning groups."""

    def __init__(self, parent, on_changed=None):
        super().__init__(parent)
        self.title("Manage Groups")
        self.geometry("720x420")
        self.minsize(640, 360)
        self.on_changed = on_changed

        self.group_name_var = tk.StringVar()
        self.contact_var = tk.StringVar()
        self.assign_group_var = tk.StringVar(value=NO_GROUP_LABEL)
        self.contact_lookup = {}
        self.group_lookup = {NO_GROUP_LABEL: None}

        self._build_layout()
        self.refresh_data()

        self.transient(parent)
        self.grab_set()

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        group_frame = ttk.LabelFrame(root, text="Groups", padding=10)
        group_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        group_frame.columnconfigure(0, weight=1)
        group_frame.rowconfigure(0, weight=1)

        self.group_tree = ttk.Treeview(
            group_frame,
            columns=("id", "name"),
            displaycolumns=("name",),
            show="headings",
            selectmode="browse",
        )
        self.group_tree.heading("name", text="Group Name")
        self.group_tree.column("name", width=220, anchor="w")
        self.group_tree.grid(row=0, column=0, sticky="nsew")
        self.group_tree.bind("<<TreeviewSelect>>", self._on_group_selected)

        group_scroll = ttk.Scrollbar(
            group_frame, orient="vertical", command=self.group_tree.yview
        )
        group_scroll.grid(row=0, column=1, sticky="ns")
        self.group_tree.configure(yscrollcommand=group_scroll.set)

        ttk.Label(group_frame, text="Group name").grid(
            row=1, column=0, sticky="w", pady=(12, 4)
        )
        ttk.Entry(group_frame, textvariable=self.group_name_var).grid(
            row=2, column=0, sticky="ew", pady=(0, 8)
        )

        group_buttons = ttk.Frame(group_frame)
        group_buttons.grid(row=3, column=0, sticky="ew")
        ttk.Button(group_buttons, text="Create", command=self._create_group).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(group_buttons, text="Rename", command=self._rename_group).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(group_buttons, text="Delete", command=self._delete_group).grid(
            row=0, column=2
        )

        assign_frame = ttk.LabelFrame(root, text="Assign Contact to Group", padding=10)
        assign_frame.grid(row=0, column=1, sticky="nsew")
        assign_frame.columnconfigure(0, weight=1)

        ttk.Label(assign_frame, text="Contact").grid(row=0, column=0, sticky="w")
        self.contact_combo = ttk.Combobox(
            assign_frame, textvariable=self.contact_var, state="readonly"
        )
        self.contact_combo.grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(assign_frame, text="Group").grid(row=2, column=0, sticky="w")
        self.assign_group_combo = ttk.Combobox(
            assign_frame, textvariable=self.assign_group_var, state="readonly"
        )
        self.assign_group_combo.grid(row=3, column=0, sticky="ew", pady=(4, 12))

        ttk.Button(
            assign_frame,
            text="Assign",
            command=self._assign_contact,
        ).grid(row=4, column=0, sticky="e")

        ttk.Button(root, text="Close", command=self.destroy).grid(
            row=1, column=1, sticky="e", pady=(12, 0)
        )

    def refresh_data(self):
        self._refresh_groups()
        self._refresh_contacts()

    def _refresh_groups(self):
        for item in self.group_tree.get_children():
            self.group_tree.delete(item)

        group_labels = [NO_GROUP_LABEL]
        self.group_lookup = {NO_GROUP_LABEL: None}
        for group in get_groups():
            self.group_tree.insert("", tk.END, values=(group["id"], group["name"]))
            label = f"{group['id']} - {group['name']}"
            group_labels.append(label)
            self.group_lookup[label] = group["id"]

        self.assign_group_combo["values"] = group_labels
        if self.assign_group_var.get() not in group_labels:
            self.assign_group_var.set(NO_GROUP_LABEL)

    def _refresh_contacts(self):
        contact_labels = []
        self.contact_lookup = {}
        for contact in get_all_contacts():
            label = f"{contact['id']} - {contact['name']} ({contact['phone']})"
            contact_labels.append(label)
            self.contact_lookup[label] = contact["id"]

        self.contact_combo["values"] = contact_labels
        if contact_labels and self.contact_var.get() not in contact_labels:
            self.contact_var.set(contact_labels[0])
        elif not contact_labels:
            self.contact_var.set("")

    def _selected_group_id(self):
        selection = self.group_tree.selection()
        if not selection:
            raise ValueError("Please select a group.")
        return int(self.group_tree.item(selection[0], "values")[0])

    def _on_group_selected(self, _event=None):
        selection = self.group_tree.selection()
        if selection:
            values = self.group_tree.item(selection[0], "values")
            self.group_name_var.set(values[1])

    def _after_group_change(self):
        self.refresh_data()
        if self.on_changed:
            self.on_changed()

    def _create_group(self):
        try:
            create_group(self.group_name_var.get())
            self.group_name_var.set("")
            self._after_group_change()
        except ValueError as exc:
            messagebox.showerror("Invalid Group", str(exc), parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create group.\n{exc}", parent=self)

    def _rename_group(self):
        try:
            group_id = self._selected_group_id()
            rename_group(group_id, self.group_name_var.get())
            self._after_group_change()
        except ValueError as exc:
            messagebox.showerror("Invalid Group", str(exc), parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not rename group.\n{exc}", parent=self)

    def _delete_group(self):
        try:
            group_id = self._selected_group_id()
            if not messagebox.askyesno(
                "Delete Group",
                "Delete this group? Contacts in the group will be kept.",
                parent=self,
            ):
                return
            delete_group(group_id)
            self.group_name_var.set("")
            self._after_group_change()
        except ValueError as exc:
            messagebox.showerror("Invalid Group", str(exc), parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not delete group.\n{exc}", parent=self)

    def _assign_contact(self):
        try:
            contact_label = self.contact_var.get()
            if contact_label not in self.contact_lookup:
                raise ValueError("Please select a contact.")
            group_id = self.group_lookup.get(self.assign_group_var.get())
            assign_contact_to_group(self.contact_lookup[contact_label], group_id)
            self._after_group_change()
            messagebox.showinfo(
                "Group Updated",
                "Contact group was updated successfully.",
                parent=self,
            )
        except ValueError as exc:
            messagebox.showerror("Invalid Assignment", str(exc), parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not assign contact.\n{exc}", parent=self)


class PhoneBookApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        init_database()
        super().__init__()
        self.title("Phone Book Management System")
        self.geometry("980x560")
        self.minsize(840, 460)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self._build_layout()
        self.refresh_contacts()

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(12, 12, 12, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Search").grid(row=0, column=0, padx=(0, 8))
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        search_entry.bind("<KeyRelease>", self._on_search_changed)

        ttk.Button(toolbar, text="Add Contact", command=self.open_add_contact).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(toolbar, text="Edit", command=self.open_edit_contact).grid(
            row=0, column=3, padx=(0, 6)
        )
        ttk.Button(toolbar, text="Delete", command=self.delete_selected_contact).grid(
            row=0, column=4, padx=(0, 6)
        )
        ttk.Button(toolbar, text="Manage Groups", command=self.open_group_manager).grid(
            row=0, column=5, padx=(0, 6)
        )
        ttk.Button(toolbar, text="Refresh", command=self.reset_search).grid(
            row=0, column=6
        )

        table_frame = ttk.Frame(self, padding=(12, 0, 12, 6))
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "phone", "email", "address", "group")
        self.contact_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            displaycolumns=("name", "phone", "email", "address", "group"),
            show="headings",
            selectmode="browse",
        )

        headings = {
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
            "address": "Address",
            "group": "Group",
        }
        widths = {
            "name": 180,
            "phone": 120,
            "email": 180,
            "address": 260,
            "group": 120,
        }
        for column, heading in headings.items():
            self.contact_tree.heading(column, text=heading)
            self.contact_tree.column(column, width=widths[column], anchor="w")

        self.contact_tree.grid(row=0, column=0, sticky="nsew")
        self.contact_tree.bind("<Double-1>", self.open_edit_contact)

        y_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.contact_tree.yview
        )
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.contact_tree.configure(yscrollcommand=y_scroll.set)

        status_bar = ttk.Frame(self, padding=(12, 0, 12, 10))
        status_bar.grid(row=2, column=0, sticky="ew")
        ttk.Label(status_bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def refresh_contacts(self, rows=None):
        try:
            contacts = get_all_contacts() if rows is None else rows
            for item in self.contact_tree.get_children():
                self.contact_tree.delete(item)

            for contact in contacts:
                self.contact_tree.insert(
                    "",
                    tk.END,
                    values=(
                        contact["id"],
                        contact["name"],
                        contact["phone"],
                        _value_or_empty(contact["email"]),
                        _value_or_empty(contact["address"]),
                        _value_or_empty(contact["group_name"]),
                    ),
                )

            self.status_var.set(f"{len(contacts)} contact(s)")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not load contacts.\n{exc}", parent=self)

    def reset_search(self):
        self.search_var.set("")
        self.refresh_contacts()

    def _on_search_changed(self, _event=None):
        keyword = self.search_var.get().strip()
        try:
            if keyword:
                self.refresh_contacts(search_contacts(keyword))
            else:
                self.refresh_contacts()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not search contacts.\n{exc}", parent=self)

    def _selected_contact_id(self):
        selection = self.contact_tree.selection()
        if not selection:
            messagebox.showwarning("No Contact Selected", "Please select a contact.", parent=self)
            return None
        values = self.contact_tree.item(selection[0], "values")
        return int(values[0])

    def _selected_contact(self):
        contact_id = self._selected_contact_id()
        if contact_id is None:
            return None
        contact = get_contact_by_id(contact_id)
        if contact is None:
            messagebox.showerror("Not Found", "The selected contact no longer exists.", parent=self)
            self.refresh_contacts()
        return contact

    def open_add_contact(self):
        ContactFormDialog(self, "Add Contact", on_saved=self.refresh_contacts)

    def open_edit_contact(self, _event=None):
        contact = self._selected_contact()
        if contact:
            ContactFormDialog(
                self,
                "Edit Contact",
                contact=contact,
                on_saved=self.refresh_contacts,
            )

    def delete_selected_contact(self):
        contact = self._selected_contact()
        if not contact:
            return
        if not messagebox.askyesno(
            "Delete Contact",
            f"Delete contact '{contact['name']}'?",
            parent=self,
        ):
            return
        try:
            remove_contact(contact["id"])
            self.refresh_contacts()
            messagebox.showinfo(
                "Contact Deleted",
                "Contact was deleted successfully.",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Could not delete contact.\n{exc}", parent=self)

    def open_group_manager(self):
        GroupManagerDialog(self, on_changed=self.refresh_contacts)


def main():
    """Start the desktop application."""
    app = PhoneBookApp()
    app.mainloop()


if __name__ == "__main__":
    main()
