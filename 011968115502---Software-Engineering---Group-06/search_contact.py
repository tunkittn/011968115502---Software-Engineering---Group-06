"""Search-contact workflow."""

import database


def search_contacts(keyword):
    """Search by contact name, phone number, or group name."""
    if not keyword or not keyword.strip():
        raise ValueError("Please enter a search keyword.")
    return database.search_contacts(keyword)
