"""Contact model used by the phone book application."""

from dataclasses import dataclass


@dataclass
class Contact:
    """Represents one contact record in the phone book."""

    contact_id: int | None
    name: str
    phone_number: str
    email: str = ""
    address: str = ""
    group_id: int | None = None
    group_name: str = ""

    @classmethod
    def from_row(cls, row):
        """Build a Contact object from a sqlite3.Row or mapping."""
        return cls(
            contact_id=row["id"],
            name=row["name"],
            phone_number=row["phone"],
            email=row["email"] or "",
            address=row["address"] or "",
            group_id=row["group_id"],
            group_name=row["group_name"] or "",
        )

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_phone_number(self):
        return self.phone_number

    def set_phone_number(self, phone):
        self.phone_number = phone

    def get_email(self):
        return self.email

    def set_email(self, email):
        self.email = email

    def get_address(self):
        return self.address

    def set_address(self, address):
        self.address = address
