"""Group management workflows."""

import database


def _clean_group_name(group_name):
    if not group_name or not group_name.strip():
        raise ValueError("Group name must not be empty.")
    return group_name.strip()


def create_group(group_name):
    """Create a new contact group."""
    return database.create_group(_clean_group_name(group_name))


def delete_group(group_id):
    """Delete a group by id."""
    affected_rows = database.delete_group(group_id)
    if affected_rows == 0:
        raise ValueError("Group not found.")
    return affected_rows


def rename_group(group_id, new_name):
    """Rename an existing group."""
    affected_rows = database.rename_group(group_id, _clean_group_name(new_name))
    if affected_rows == 0:
        raise ValueError("Group not found.")
    return affected_rows


def assign_contact_to_group(contact_id, group_id):
    """Assign a contact to a group, or clear the group with None."""
    affected_rows = database.assign_contact_to_group(contact_id, group_id)
    if affected_rows == 0:
        raise ValueError("Contact not found.")
    return affected_rows


def get_contacts_by_group(group_id):
    """Return contacts that belong to a group."""
    return database.get_contacts_by_group(group_id)


def get_groups():
    """Return all groups."""
    return database.get_all_groups()
