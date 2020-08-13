import ipaddress
import json
import pathlib
import shutil
import tempfile
import unittest

import httpretty

from freenom_dns_updater import EncryptedString


class EncryptTringTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_encrypt(self):
        with EncryptedString(b"testing").ensure_encrypted() as s:
            self.assertNotEqual(b"testing", s.data)

    def test_encrypt_then_decrypt(self):
        with EncryptedString(b"testing").ensure_encrypted() as s:
            self.assertEqual("testing", s.str())
            self.assertEqual(b"testing", s.bytes())

    def test_encrypt_then_decrypt_empty_string(self):
        with EncryptedString("").ensure_encrypted() as s:
            self.assertEqual("", s.str())
            self.assertEqual(b"", s.bytes())

    def test_using_invalidate_the_data(self):
        with EncryptedString(b"testing").ensure_encrypted() as s:
            pass
        with self.assertRaises(Exception) as cm:
            s.str()

if __name__ == '__main__':
    unittest.main()
