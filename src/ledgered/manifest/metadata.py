import re
from dataclasses import dataclass

from ledgered.serializers import Jsonable, JsonList

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_string(key: str, value: object, required: bool) -> None:
    if value is None and not required:
        return
    if not isinstance(value, str):
        raise ValueError(f"Metadata '{key} = {value}' should be a string, not a {type(value)}")
    if not value:
        raise ValueError(f"Metadata '{key}' should not be empty")


@dataclass
class MetadataConfig(Jsonable):
    author: str
    contact: str
    publisher: str | None
    support_url: str | None
    compatible_wallets: JsonList | None

    def __init__(
        self,
        author: str,
        contact: str,
        publisher: str | None = None,
        support_url: str | None = None,
        compatible_wallets: list[str] | None = None,
    ) -> None:
        _check_string("author", author, required=True)
        _check_string("contact", contact, required=True)
        if not EMAIL_PATTERN.match(contact):
            raise ValueError(f"Metadata 'contact = {contact}' should be an email address")
        _check_string("publisher", publisher, required=False)
        _check_string("support_url", support_url, required=False)
        self.author = author
        self.contact = contact
        self.publisher = publisher
        self.support_url = support_url

        if compatible_wallets is None:
            self.compatible_wallets = None
        elif not isinstance(compatible_wallets, list) or not all(isinstance(w, str) for w in compatible_wallets):
            raise ValueError(f"Metadata 'compatible_wallets = {compatible_wallets}' should be a list of strings")
        else:
            self.compatible_wallets = JsonList(compatible_wallets)
