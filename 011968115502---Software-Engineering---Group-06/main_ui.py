"""Flet user interface for the Phone Book Management System."""

import flet as ft

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

BG = "#F5F7FA"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F8FAFC"
BORDER = "#D7DEE8"
TEXT = "#1F2937"
MUTED = "#64748B"
TEAL = "#0F766E"
TEAL_LIGHT = "#CCFBF1"
BLUE = "#2563EB"
GREEN = "#15803D"
AMBER = "#B45309"
RED = "#B91C1C"
CENTER = ft.Alignment(0, 0)


def _value_or_empty(value):
    return "" if value is None else str(value)


def _safe_text(value):
    return _value_or_empty(value) or "-"


def _group_value(group_id):
    return "" if group_id in ("", None) else str(group_id)


def _parse_group_id(value):
    return None if value in ("", None) else int(value)


def _contact_group(contact):
    return ", ".join([g["name"] for g in contact.get("groups", [])]) or "-"


def _dialog_title(icon, title):
    return ft.Row(
        [
            ft.Container(
                ft.Icon(icon, color=TEAL, size=20),
                width=36,
                height=36,
                border_radius=8,
                bgcolor=TEAL_LIGHT,
                alignment=CENTER,
            ),
            ft.Text(title, size=20, weight=ft.FontWeight.W_700, color=TEXT),
        ],
        spacing=10,
    )


def _field(label, icon, value="", **kwargs):
    return ft.TextField(
        label=label,
        value=value or "",
        prefix_icon=icon,
        border_radius=8,
        border_color=BORDER,
        focused_border_color=TEAL,
        filled=True,
        fill_color=SURFACE_MUTED,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        **kwargs,
    )


def _dropdown(label, value, options, icon=ft.Icons.BADGE_OUTLINED):
    return ft.Dropdown(
        label=label,
        value=value,
        options=options,
        leading_icon=icon,
        border_radius=8,
        border_color=BORDER,
        focused_border_color=TEAL,
        filled=True,
        fill_color=SURFACE_MUTED,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        enable_search=True,
    )


def _button_style(bgcolor=None, color=None):
    return ft.ButtonStyle(
        bgcolor=bgcolor,
        color=color,
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )


def _metric_card(label, value_control, icon, color, on_click=None):
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    ft.Icon(icon, size=20, color=color),
                    width=40,
                    height=40,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.10, color),
                    alignment=CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(label, size=12, color=MUTED),
                        value_control,
                    ],
                    spacing=0,
                    tight=True,
                ),
            ],
            spacing=12,
        ),
        padding=16,
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        expand=True,
        on_click=on_click,
        ink=True,
    )


def _make_group_options(include_no_group=True):
    options = []
    if include_no_group:
        options.append(ft.DropdownOption(key="", text=NO_GROUP_LABEL))
    for group in get_groups():
        options.append(ft.DropdownOption(key=str(group["id"]), text=group["name"]))
    return options


def _make_contact_options():
    return [
        ft.DropdownOption(
            key=str(contact["id"]),
            text=f"{contact['name']} - {contact['phone']}",
        )
        for contact in get_all_contacts()
    ]


def _show_snack(page, message, color=TEAL):
    page.show_dialog(
        ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
        )
    )


def _show_error(page, message):
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=_dialog_title(ft.Icons.ERROR_OUTLINE, "Error"),
            content=ft.Text(message, color=TEXT),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: page.pop_dialog()),
            ],
        )
    )


def main():
    """Start the Flet desktop application."""
    ft.app(target=_build_app, view=ft.AppView.FLET_APP)


def _build_app(page: ft.Page):
    init_database()

    page.title = "Phone Book Management System"
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=TEAL)

    state = {
        "contacts": [],
        "selected_contact_id": None,
        "search": "",
        "filter_group_id": None,
        "filter_group_name": None,
    }

    search_field = ft.TextField(
        hint_text="Search by name, phone, or group",
        prefix_icon=ft.Icons.SEARCH,
        height=54,
        max_lines=1,
        expand=True,
        border_radius=8,
        border_color=BORDER,
        focused_border_color=TEAL,
        filled=True,
        fill_color=SURFACE_MUTED,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        on_change=lambda _e: refresh_contacts(),
    )
    contact_count_text = ft.Text("0", size=22, weight=ft.FontWeight.W_700, color=TEXT)
    group_count_text = ft.Text("0", size=22, weight=ft.FontWeight.W_700, color=TEXT)
    selected_count_text = ft.Text(
        "None",
        size=22,
        weight=ft.FontWeight.W_700,
        color=TEXT,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    detail_name = ft.Text(
        "Select a contact",
        size=20,
        weight=ft.FontWeight.W_700,
        color=TEXT,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    detail_phone = ft.Text(
        "-",
        size=14,
        color=MUTED,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )
    detail_email = ft.Text(
        "-",
        size=14,
        color=MUTED,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )
    detail_address = ft.Text(
        "-",
        size=14,
        color=MUTED,
        max_lines=3,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )
    detail_group = ft.Text(
        "-",
        size=14,
        color=MUTED,
        expand=True,
    )

    table_area = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    def selected_contact():
        contact_id = state["selected_contact_id"]
        if contact_id is None:
            return None
        return get_contact_by_id(contact_id)

    def select_contact(contact_id):
        state["selected_contact_id"] = contact_id
        render_table()
        render_detail()
        page.update()

    def render_detail():
        contact = selected_contact()
        if not contact:
            detail_name.value = "Select a contact"
            detail_phone.value = "-"
            detail_email.value = "-"
            detail_address.value = "-"
            detail_group.value = "-"
            selected_count_text.value = "None"
            return

        detail_name.value = contact["name"]
        detail_phone.value = contact["phone"]
        detail_email.value = _safe_text(contact["email"])
        detail_address.value = _safe_text(contact["address"])
        detail_group.value = _contact_group(contact)
        selected_count_text.value = contact["name"]

    def make_table_text(value, *, color=TEXT, weight=None, max_lines=1):
        return ft.Text(
            _safe_text(value),
            size=13,
            color=color,
            weight=weight,
            max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS if max_lines is not None else None,
        )

    def make_table_cell(content, expand, *, bgcolor=None, on_click=None):
        return ft.Container(
            content=content,
            expand=expand,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=bgcolor,
            on_click=on_click,
        )

    # Vietnamese alphabet order including accented characters
    VIETNAMESE_ALPHABET = "AĂÂBCDĐEÊFGHIJKLMNOÔƠPQRSTUƯVWXYZ#"

    def get_sort_key(contact):
        """Get the first letter of contact name for sorting using Vietnamese alphabet order."""
        if not contact["name"]:
            return (999, "")
        first_char = contact["name"].upper()[0]
        # Get the position in Vietnamese alphabet, or put at end if not found
        position = VIETNAMESE_ALPHABET.find(first_char)
        if position == -1:
            position = 999  # Put unknown characters at the end
        return (position, contact["name"].upper())

    def get_display_letter(char):
        """Get the display letter for section headers."""
        upper_char = char.upper()
        if upper_char in VIETNAMESE_ALPHABET:
            return upper_char
        return "#"

    def render_table():
        column_specs = [
            ("Name", 20),
            ("Phone", 14),
            ("Email", 24),
            ("Address", 22),
            ("Group", 24),
        ]

        table_rows = [
            ft.Container(
                content=ft.Row(
                    [
                        make_table_cell(
                            make_table_text(
                                label,
                                weight=ft.FontWeight.W_700,
                                color=TEXT,
                            ),
                            expand,
                        )
                        for label, expand in column_specs
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                bgcolor=ft.Colors.GREY_100,
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                height=48,
            )
        ]

        # Sort contacts using Vietnamese alphabet order
        sorted_contacts = sorted(state["contacts"], key=get_sort_key)
        
        # Group contacts by first letter
        current_letter = None
        for contact in sorted_contacts:
            contact_letter = get_display_letter(contact["name"][0] if contact["name"] else "")
            
            # Add section header when letter changes
            if contact_letter != current_letter:
                current_letter = contact_letter
                table_rows.append(
                    ft.Container(
                        content=ft.Text(
                            current_letter,
                            size=14,
                            weight=ft.FontWeight.W_700,
                            color=TEAL,
                        ),
                        bgcolor="#F0FDFB",
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        border=ft.border.only(top=ft.BorderSide(1, BORDER)),
                    )
                )
            
            contact_id = contact["id"]
            row_bgcolor = TEAL_LIGHT if state["selected_contact_id"] == contact_id else SURFACE
            row_border_color = "#A7F3D0" if state["selected_contact_id"] == contact_id else BORDER

            table_rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            make_table_cell(
                                make_table_text(contact["name"]),
                                20,
                                bgcolor=row_bgcolor,
                                on_click=lambda _e, cid=contact_id: select_contact(cid),
                            ),
                            make_table_cell(
                                make_table_text(contact["phone"]),
                                14,
                                bgcolor=row_bgcolor,
                                on_click=lambda _e, cid=contact_id: select_contact(cid),
                            ),
                            make_table_cell(
                                make_table_text(_safe_text(contact["email"])),
                                24,
                                bgcolor=row_bgcolor,
                                on_click=lambda _e, cid=contact_id: select_contact(cid),
                            ),
                            make_table_cell(
                                make_table_text(_safe_text(contact["address"])),
                                22,
                                bgcolor=row_bgcolor,
                                on_click=lambda _e, cid=contact_id: select_contact(cid),
                            ),
                            make_table_cell(
                                make_table_text(_contact_group(contact), max_lines=None),
                                24,
                                bgcolor=row_bgcolor,
                                on_click=lambda _e, cid=contact_id: select_contact(cid),
                            ),
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, row_border_color)),
                    bgcolor=row_bgcolor,
                    height=48,
                    ink=True,
                    on_click=lambda _e, cid=contact_id: select_contact(cid),
                )
            )

        if len(table_rows) == 1:
            table_rows.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.CONTACT_PHONE_OUTLINED, size=48, color=MUTED),
                            ft.Text("No contacts found", size=18, weight=ft.FontWeight.W_600),
                            ft.Text(
                                "Add a contact or clear the search field.",
                                size=13,
                                color=MUTED,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    height=280,
                    alignment=CENTER,
                    bgcolor=SURFACE,
                )
            )

        table_area.controls = [
            ft.Container(
                content=ft.Column(table_rows, spacing=0, expand=True),
                border=ft.border.all(1, BORDER),
                border_radius=8,
                bgcolor=SURFACE,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
            )
        ]

        # Update table panel column
        table_panel_column = table_panel.content
        if state["filter_group_id"] is not None:
            # Show filter indicator
            table_panel_column.controls[1] = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO, size=16, color=BLUE),
                        ft.Text(
                            "Viewing group: ",
                            size=13,
                            color=BLUE,
                        ),
                        ft.Text(
                            state.get("filter_group_name", ""),
                            size=13,
                            color=BLUE,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Container(expand=True),
                        ft.TextButton(
                            "View All",
                            icon=ft.Icons.CLOSE,
                            on_click=view_all_contacts,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.Colors.with_opacity(0.1, BLUE),
                border_radius=6,
            )
        else:
            # Hide filter indicator by replacing with empty container
            table_panel_column.controls[1] = ft.Container(height=0)

    def refresh_contacts():
        keyword = search_field.value.strip()
        state["search"] = keyword
        try:
            state["contacts"] = search_contacts(keyword) if keyword else get_all_contacts()
        except ValueError:
            state["contacts"] = []
        except Exception as exc:
            _show_error(page, f"Could not load contacts.\n{exc}")
            state["contacts"] = []

        # Apply group filter if set
        if state["filter_group_id"] is not None:
            state["contacts"] = [c for c in state["contacts"] if c.get("group_id") == state["filter_group_id"]]

        contact_ids = {contact["id"] for contact in state["contacts"]}
        if state["selected_contact_id"] not in contact_ids:
            state["selected_contact_id"] = state["contacts"][0]["id"] if state["contacts"] else None

        contact_count_text.value = str(len(state["contacts"]))
        group_count_text.value = str(len(get_groups()))
        render_table()
        render_detail()
        page.update()

    def reset_search(_e=None):
        search_field.value = ""
        state["filter_group_id"] = None
        state["filter_group_name"] = None
        refresh_contacts()

    def view_all_contacts(_e=None):
        """Clear filter and view all contacts."""
        state["filter_group_id"] = None
        state["filter_group_name"] = None
        search_field.value = ""
        refresh_contacts()

    def open_contact_form(contact=None):
        is_edit = contact is not None
        name_field = _field(
            "Name",
            ft.Icons.PERSON_OUTLINE,
            value=contact["name"] if is_edit else "",
            autofocus=True,
        )
        phone_field = _field(
            "Phone",
            ft.Icons.PHONE_OUTLINED,
            value=contact["phone"] if is_edit else "",
            keyboard_type=ft.KeyboardType.PHONE,
            max_length=11,
        )
        email_field = _field(
            "Email",
            ft.Icons.MAIL_OUTLINE,
            value=contact["email"] if is_edit else "",
            keyboard_type=ft.KeyboardType.EMAIL,
        )
        address_field = _field(
            "Address",
            ft.Icons.HOME_OUTLINED,
            value=contact["address"] if is_edit else "",
        )
        group_field = _dropdown(
            "Group",
            _group_value(contact["group_id"]) if is_edit else "",
            _make_group_options(include_no_group=True),
        )
        error_text = ft.Text("", color=RED, visible=False, size=13)

        def close_dialog(_e=None):
            page.pop_dialog()

        def save_contact(_e=None):
            try:
                group_id = _parse_group_id(group_field.value)
                if is_edit:
                    edit_contact(
                        contact["id"],
                        name_field.value,
                        phone_field.value,
                        email_field.value,
                        address_field.value,
                        group_id,
                    )
                    message = "Contact updated successfully."
                else:
                    add_contact(
                        name_field.value,
                        phone_field.value,
                        email_field.value,
                        address_field.value,
                        group_id,
                    )
                    message = "Contact added successfully."

                page.pop_dialog()
                refresh_contacts()
                _show_snack(page, message, GREEN)
            except ValueError as exc:
                error_text.value = str(exc)
                error_text.visible = True
                dialog.update()
            except Exception as exc:
                error_text.value = f"Could not save contact. {exc}"
                error_text.visible = True
                dialog.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=_dialog_title(
                ft.Icons.EDIT_OUTLINED if is_edit else ft.Icons.PERSON_ADD_ALT_1,
                "Edit Contact" if is_edit else "Add Contact",
            ),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    [
                        ft.ResponsiveRow(
                            [
                                ft.Container(name_field, col={"sm": 12, "md": 6}),
                                ft.Container(phone_field, col={"sm": 12, "md": 6}),
                                ft.Container(email_field, col={"sm": 12, "md": 6}),
                                ft.Container(group_field, col={"sm": 12, "md": 6}),
                            ],
                            spacing=10,
                            run_spacing=10,
                        ),
                        address_field,
                        error_text,
                    ],
                    tight=True,
                    spacing=12,
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.FilledButton(
                    "Save",
                    icon=ft.Icons.SAVE_OUTLINED,
                    style=_button_style(TEAL, ft.Colors.WHITE),
                    on_click=save_contact,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def open_add_contact(_e=None):
        open_contact_form()

    def open_edit_contact(_e=None):
        contact = selected_contact()
        if not contact:
            _show_snack(page, "Select a contact first.", AMBER)
            return
        open_contact_form(contact)

    def delete_selected_contact(_e=None):
        contact = selected_contact()
        if not contact:
            _show_snack(page, "Select a contact first.", AMBER)
            return

        def close_dialog(_e=None):
            page.pop_dialog()

        def do_delete(_e=None):
            try:
                remove_contact(contact["id"])
                page.pop_dialog()
                refresh_contacts()
                _show_snack(page, "Contact deleted successfully.", GREEN)
            except Exception as exc:
                page.pop_dialog()
                _show_error(page, f"Could not delete contact.\n{exc}")

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=_dialog_title(ft.Icons.DELETE_OUTLINE, "Delete Contact"),
                content=ft.Text(
                    f"Delete '{contact['name']}' from the phone book?",
                    color=TEXT,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.FilledButton(
                        "Delete",
                        icon=ft.Icons.DELETE_OUTLINE,
                        style=_button_style(RED, ft.Colors.WHITE),
                        on_click=do_delete,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def open_group_manager(_e=None):
        selected_group = {"id": None}
        group_name_field = _field("Group name", ft.Icons.GROUP_OUTLINED)
        group_list = ft.ListView(expand=True, spacing=8, padding=0)
        selected_contacts = {}  # Dictionary to track checkbox states: contact_id -> checked
        contact_list = ft.ListView(expand=True, spacing=0, padding=0)
        assign_group_field = _dropdown(
            "Group",
            "",
            _make_group_options(include_no_group=True),
        )
        error_text = ft.Text("", color=RED, size=13, visible=False)
        search_contacts_field = ft.TextField(
            hint_text="Search by name or phone...",
            prefix_icon=ft.Icons.SEARCH,
            height=44,
            max_lines=1,
            border_radius=8,
            border_color=BORDER,
            focused_border_color=TEAL,
            filled=True,
            fill_color=SURFACE_MUTED,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )

        def set_error(message):
            error_text.value = message
            error_text.visible = bool(message)
            dialog.update()

        def filter_contacts_by_search(search_keyword=""):
            """Filter contacts based on search keyword (name or phone)."""
            if not search_keyword or not search_keyword.strip():
                return get_all_contacts()
            
            keyword = search_keyword.strip().lower()
            filtered = []
            for contact in get_all_contacts():
                if (keyword in contact["name"].lower() or 
                    keyword in contact["phone"].lower()):
                    filtered.append(contact)
            return filtered

        def render_contacts_list(_e=None):
            """Render contact list based on current search."""
            contact_list.controls = []
            filtered_contacts = filter_contacts_by_search(search_contacts_field.value)
            
            if not filtered_contacts:
                contact_list.controls.append(
                    ft.Container(
                        content=ft.Text("No contacts found.", color=MUTED),
                        alignment=CENTER,
                        height=100,
                    )
                )
            else:
                for contact in filtered_contacts:
                    contact_id = contact["id"]
                    is_checked = selected_contacts.get(contact_id, False)
                    
                    def toggle_contact(e, cid=contact_id):
                        selected_contacts[cid] = e.control.value
                        dialog.update()
                    
                    checkbox = ft.Checkbox(
                        label=f"{contact['name']} - {contact['phone']}",
                        value=is_checked,
                        on_change=toggle_contact,
                    )
                    contact_list.controls.append(checkbox)
            
            # Only update dialog if it's been added to the page
            try:
                dialog.update()
            except:
                pass

        # Attach the on_change event after render_contacts_list is defined
        search_contacts_field.on_change = render_contacts_list

        def render_groups():
            contacts = get_all_contacts()
            counts = {}
            for item in contacts:
                for group in item.get("groups", []):
                    group_id = group["id"]
                    counts[group_id] = counts.get(group_id, 0) + 1

            controls = []
            for group in get_groups():
                is_selected = selected_group["id"] == group["id"]

                def choose_group(_e, group_id=group["id"], group_name=group["name"]):
                    selected_group["id"] = group_id
                    group_name_field.value = group_name
                    render_groups()
                    dialog.update()

                def view_group_contacts(_e, group_id=group["id"]):
                    page.pop_dialog()
                    # Filter contacts by group - check if contact has this group in its groups list
                    filtered = [c for c in get_all_contacts() if any(g["id"] == group_id for g in c.get("groups", []))]
                    state["contacts"] = filtered
                    if filtered:
                        state["selected_contact_id"] = filtered[0]["id"]
                    else:
                        state["selected_contact_id"] = None
                    contact_count_text.value = str(len(filtered))
                    render_table()
                    render_detail()
                    page.update()

                controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.GROUP_OUTLINED, color=TEAL if is_selected else MUTED),
                                ft.Column(
                                    [
                                        ft.Text(group["name"], weight=ft.FontWeight.W_600, color=TEXT),
                                        ft.Text(
                                            f"{counts.get(group['id'], 0)} contact(s)",
                                            size=12,
                                            color=MUTED,
                                        ),
                                    ],
                                    spacing=0,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=12,
                        border_radius=8,
                        bgcolor=TEAL_LIGHT if is_selected else SURFACE_MUTED,
                        border=ft.border.all(1, TEAL if is_selected else BORDER),
                        on_click=choose_group,
                        data=group["id"],
                    )
                )

            if not controls:
                controls.append(
                    ft.Container(
                        content=ft.Text("No groups yet.", color=MUTED),
                        alignment=CENTER,
                        height=140,
                    )
                )
            group_list.controls = controls

        def refresh_group_dialog(update_dialog=True):
            # Refresh contact list with checkboxes
            render_contacts_list()

            assign_group_field.options = _make_group_options(include_no_group=True)
            if assign_group_field.value not in [option.key for option in assign_group_field.options]:
                assign_group_field.value = ""

            render_groups()
            refresh_contacts()
            if update_dialog:
                dialog.update()

        def create_new_group(_e=None):
            try:
                create_group(group_name_field.value)
                group_name_field.value = ""
                selected_group["id"] = None
                set_error("")
                refresh_group_dialog()
                _show_snack(page, "Group created successfully.", GREEN)
            except ValueError as exc:
                set_error(str(exc))
            except Exception as exc:
                set_error(f"Could not create group. {exc}")

        def rename_selected_group(_e=None):
            if not selected_group["id"]:
                set_error("Select a group to rename.")
                return
            try:
                rename_group(selected_group["id"], group_name_field.value)
                set_error("")
                refresh_group_dialog()
                _show_snack(page, "Group renamed successfully.", GREEN)
            except ValueError as exc:
                set_error(str(exc))
            except Exception as exc:
                set_error(f"Could not rename group. {exc}")

        def delete_selected_group(_e=None):
            if not selected_group["id"]:
                set_error("Select a group to delete.")
                return
            try:
                delete_group(selected_group["id"])
                selected_group["id"] = None
                group_name_field.value = ""
                set_error("")
                refresh_group_dialog()
                _show_snack(page, "Group deleted successfully.", GREEN)
            except ValueError as exc:
                set_error(str(exc))
            except Exception as exc:
                set_error(f"Could not delete group. {exc}")

        def assign_group(_e=None):
            # Get all selected contacts
            selected_contact_ids = [cid for cid, checked in selected_contacts.items() if checked]
            
            if not selected_contact_ids:
                set_error("Select at least one contact first.")
                return
            try:
                # Assign all selected contacts to the group
                for contact_id in selected_contact_ids:
                    assign_contact_to_group(
                        contact_id,
                        _parse_group_id(assign_group_field.value),
                    )
                set_error("")
                selected_contacts.clear()
                refresh_group_dialog()
                _show_snack(page, f"Successfully assigned {len(selected_contact_ids)} contact(s) to group.", GREEN)
            except ValueError as exc:
                set_error(str(exc))
            except Exception as exc:
                set_error(f"Could not assign contact(s). {exc}")

        dialog = ft.AlertDialog(
            modal=True,
            title=_dialog_title(ft.Icons.GROUP_OUTLINED, "Manage Groups"),
            content=ft.Container(
                width=820,
                height=500,
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Groups", size=14, weight=ft.FontWeight.W_700, color=TEXT),
                                    group_list,
                                    group_name_field,
                                    ft.Row(
                                        [
                                            ft.FilledButton(
                                                "Create",
                                                icon=ft.Icons.ADD,
                                                style=_button_style(TEAL, ft.Colors.WHITE),
                                                on_click=create_new_group,
                                            ),
                                            ft.OutlinedButton(
                                                "Rename",
                                                icon=ft.Icons.EDIT_OUTLINED,
                                                on_click=rename_selected_group,
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color=RED,
                                                tooltip="Delete group",
                                                on_click=delete_selected_group,
                                            ),
                                        ],
                                        spacing=8,
                                        wrap=True,
                                    ),
                                ],
                                spacing=12,
                                expand=True,
                            ),
                            expand=1,
                        ),
                        ft.VerticalDivider(width=1, color=BORDER),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "Assign Contacts",
                                        size=14,
                                        weight=ft.FontWeight.W_700,
                                        color=TEXT,
                                    ),
                                    ft.Text(
                                        "Select contacts to assign (check boxes below):",
                                        size=12,
                                        color=MUTED,
                                    ),
                                    search_contacts_field,
                                    contact_list,
                                    ft.Divider(color=BORDER),
                                    assign_group_field,
                                    ft.FilledButton(
                                        "Apply Group",
                                        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                        style=_button_style(BLUE, ft.Colors.WHITE),
                                        on_click=assign_group,
                                    ),
                                    ft.Divider(color=BORDER),
                                    ft.Text(
                                        "Double-click a group to view its contacts. Deleting a group keeps its contacts and clears their group.",
                                        size=12,
                                        color=MUTED,
                                    ),
                                    error_text,
                                ],
                                spacing=12,
                            ),
                            expand=1,
                        ),
                    ],
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: page.pop_dialog()),
            ],
        )

        refresh_group_dialog(update_dialog=False)
        page.show_dialog(dialog)

    def open_group_list(_e=None):
        """Show a simple list of groups - double-click to view contacts in that group."""
        group_list = ft.ListView(expand=True, spacing=8, padding=0)

        def render_groups_list():
            contacts = get_all_contacts()
            counts = {}
            for item in contacts:
                group_id = item.get("group_id")
                counts[group_id] = counts.get(group_id, 0) + 1

            controls = []
            for group in get_groups():
                def on_double_click(_e, group_id=group["id"], group_name=group["name"]):
                    page.pop_dialog()
                    # Filter contacts by group
                    filtered = [c for c in get_all_contacts() if c.get("group_id") == group_id]
                    state["contacts"] = filtered
                    state["filter_group_id"] = group_id
                    state["filter_group_name"] = group_name
                    if filtered:
                        state["selected_contact_id"] = filtered[0]["id"]
                    else:
                        state["selected_contact_id"] = None
                    contact_count_text.value = str(len(filtered))
                    render_table()
                    render_detail()
                    page.update()

                controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.GROUP_OUTLINED, color=TEAL, size=24),
                                ft.Column(
                                    [
                                        ft.Text(group["name"], weight=ft.FontWeight.W_600, color=TEXT, size=15),
                                        ft.Text(
                                            f"{counts.get(group['id'], 0)} contact(s)",
                                            size=13,
                                            color=MUTED,
                                        ),
                                    ],
                                    spacing=0,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        border_radius=8,
                        bgcolor=SURFACE_MUTED,
                        border=ft.border.all(1, BORDER),
                        on_click=on_double_click,
                        ink=True,
                    )
                )

            if not controls:
                controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.GROUP_OUTLINED, size=48, color=MUTED),
                                ft.Text("No groups yet", size=18, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    "Create a group from 'Manage Groups'",
                                    size=13,
                                    color=MUTED,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        height=280,
                        alignment=CENTER,
                        bgcolor=SURFACE,
                    )
                )
            group_list.controls = controls

        render_groups_list()

        dialog = ft.AlertDialog(
            modal=True,
            title=_dialog_title(ft.Icons.GROUP_OUTLINED, "Select a Group"),
            content=ft.Container(
                width=450,
                height=400,
                content=group_list,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: page.pop_dialog()),
            ],
        )
        page.show_dialog(dialog)

    header = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(
                            ft.Icon(ft.Icons.CONTACT_PHONE_OUTLINED, size=26, color=ft.Colors.WHITE),
                            width=48,
                            height=48,
                            border_radius=8,
                            bgcolor=TEAL,
                            alignment=CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "Phone Book Management System",
                                    size=22,
                                    weight=ft.FontWeight.W_700,
                                    color=TEXT,
                                ),
                                ft.Text(
                                    "Manage contacts, phone numbers, and groups",
                                    size=13,
                                    color=MUTED,
                                ),
                            ],
                            spacing=0,
                            tight=True,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.FilledButton(
                            "Add Contact",
                            icon=ft.Icons.ADD,
                            style=_button_style(TEAL, ft.Colors.WHITE),
                            on_click=open_add_contact,
                        ),
                        ft.OutlinedButton(
                            "Manage Groups",
                            icon=ft.Icons.GROUP_OUTLINED,
                            on_click=open_group_manager,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=18),
        bgcolor=SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )

    metrics = ft.Row(
        [
            _metric_card("Contacts shown", contact_count_text, ft.Icons.PERSON_OUTLINE, TEAL),
            _metric_card("Groups", group_count_text, ft.Icons.GROUP_OUTLINED, BLUE, on_click=open_group_list),
            _metric_card("Selected", selected_count_text, ft.Icons.CHECK_CIRCLE_OUTLINE, GREEN),
        ],
        spacing=12,
    )

    table_panel = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Contacts", size=16, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    tooltip="Edit selected contact",
                                    on_click=open_edit_contact,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=RED,
                                    tooltip="Delete selected contact",
                                    on_click=delete_selected_contact,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    tooltip="Clear search and refresh",
                                    on_click=reset_search,
                                ),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO, size=16, color=BLUE),
                            ft.Text(
                                "Viewing group: ",
                                size=13,
                                color=BLUE,
                            ),
                            ft.Text(
                                state.get("filter_group_name", ""),
                                size=13,
                                color=BLUE,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "View All",
                                icon=ft.Icons.CLOSE,
                                on_click=view_all_contacts,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=ft.Colors.with_opacity(0.1, BLUE),
                    border_radius=6,
                    visible=state["filter_group_id"] is not None,
                ),
                ft.Row([search_field], spacing=0),
                ft.Container(
                    content=table_area,
                    expand=True,
                    border=ft.border.all(1, BORDER),
                    border_radius=8,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    bgcolor=SURFACE,
                ),
            ],
            spacing=12,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=18,
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        expand=3,
    )

    detail_panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("Contact Details", size=16, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Divider(color=BORDER),
                detail_name,
                ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.PHONE_OUTLINED, size=18, color=TEAL), detail_phone]),
                        ft.Row([ft.Icon(ft.Icons.MAIL_OUTLINE, size=18, color=BLUE), detail_email]),
                        ft.Row([ft.Icon(ft.Icons.HOME_OUTLINED, size=18, color=AMBER), detail_address]),
                        ft.Row([ft.Icon(ft.Icons.GROUP_OUTLINED, size=18, color=GREEN), detail_group]),
                    ],
                    spacing=10,
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    "Edit Contact",
                    icon=ft.Icons.EDIT_OUTLINED,
                    style=_button_style(TEAL, ft.Colors.WHITE),
                    on_click=open_edit_contact,
                    width=220,
                ),
                ft.OutlinedButton(
                    "Delete Contact",
                    icon=ft.Icons.DELETE_OUTLINE,
                    on_click=delete_selected_contact,
                    width=220,
                ),
            ],
            spacing=14,
            expand=True,
        ),
        padding=18,
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        expand=1,
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            metrics,
                            ft.Row(
                                [table_panel, detail_panel],
                                spacing=12,
                                expand=True,
                                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                            ),
                        ],
                        spacing=12,
                        expand=True,
                    ),
                    padding=18,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )

    refresh_contacts()


if __name__ == "__main__":
    main()
