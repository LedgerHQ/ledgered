from unittest import TestCase

from ledgered.manifest.metadata import MetadataConfig


class TestMetadataConfig(TestCase):
    def setUp(self):
        self.required = {"author": "Ledger", "contact": "support@ledger.com"}
        self.fields = {
            **self.required,
            "publisher": "Ledger",
            "support_url": "https://support.ledger.com",
            "compatible_wallets": ["Ledger Wallet"],
        }

    def test___init__ok(self):
        config = MetadataConfig(**self.fields)
        for key, value in self.fields.items():
            self.assertEqual(getattr(config, key), value)

    def test___init__required_only(self):
        config = MetadataConfig(**self.required)
        self.assertEqual(config.author, "Ledger")
        self.assertEqual(config.contact, "support@ledger.com")
        self.assertIsNone(config.publisher)
        self.assertIsNone(config.support_url)
        self.assertIsNone(config.compatible_wallets)

    def test___init__nok_missing_required(self):
        with self.assertRaises(TypeError):
            MetadataConfig(author="Ledger")
        with self.assertRaises(TypeError):
            MetadataConfig(contact="support@ledger.com")

    def test___init__nok_empty_required(self):
        with self.assertRaises(ValueError):
            MetadataConfig(author="", contact="support@ledger.com")

    def test___init__nok_contact_not_email(self):
        for contact in ("https://support.ledger.com", "support", "support@ledger", "a b@ledger.com"):
            with self.assertRaises(ValueError):
                MetadataConfig(author="Ledger", contact=contact)

    def test___init__nok_string_type(self):
        with self.assertRaises(ValueError):
            MetadataConfig(author=3, contact="support@ledger.com")
        with self.assertRaises(ValueError):
            MetadataConfig(**self.required, publisher=3)

    def test___init__nok_wallets_type(self):
        with self.assertRaises(ValueError):
            MetadataConfig(**self.required, compatible_wallets="Ledger Wallet")
        with self.assertRaises(ValueError):
            MetadataConfig(**self.required, compatible_wallets=["Ledger Wallet", 3])

    def test___init__nok_unknown_key(self):
        with self.assertRaises(TypeError):
            MetadataConfig(**self.required, copyright="(c) Ledger")

    def test_json(self):
        self.assertEqual(MetadataConfig(**self.fields).json, self.fields)
