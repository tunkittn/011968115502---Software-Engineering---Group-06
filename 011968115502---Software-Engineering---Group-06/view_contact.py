"""View-contact workflow."""

import database


def get_all_contacts():
    """Return all saved contacts."""
    return database.get_all_contacts()
