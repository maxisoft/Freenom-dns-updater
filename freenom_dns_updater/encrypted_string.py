import warnings
from base64 import b85decode, b85encode
from typing import Union, Optional

from oscrypto.symmetric import aes_cbc_pkcs7_decrypt, aes_cbc_pkcs7_encrypt

_IV = b"\xf9;\xe7k\xc6\xb3\xea=}P\x11\x18\xebMl\x87"
_KEY = b"?\x11t\xb9\xc3\xbc\xf1\xee\xf0!L9\xd0/\xbb\xd0"
_INVALID = b"Invalid"


class EncryptedString:
    magic = b'encr1+'
    magicend = b'+ypt1'

    def __init__(self, data: Union[bytes, str], key: Optional[bytes] = None, iv: Optional[bytes] = None,
                 encoding='UTF-8'):
        if isinstance(data, str):
            data = data.encode(encoding)
        self.data: bytes = data
        self.encrypted: bool = self.is_encrypted(self.data)
        self._key: bytes = key if key else _KEY
        self._iv: bytes = iv if iv else _IV

    @staticmethod
    def _check_key(key: bytes):
        if key is _KEY:
            warnings.warn("Using default key is not secure at all")

    @classmethod
    def is_encrypted(cls, data: bytes) -> bool:
        return data.startswith(cls.magic) and data.endswith(cls.magicend)

    @classmethod
    def _decrypt(cls, data: bytes, key: bytes, iv: bytes, check: bool = True) -> bytes:
        assert not check or cls.is_encrypted(data)
        cls._check_key(key)
        d: bytes = data[len(cls.magic):-len(cls.magicend)]
        d = b85decode(d)
        d = aes_cbc_pkcs7_decrypt(key, d, iv)
        assert d[-1] == 0
        return d[:-1]

    @classmethod
    def encrypt(cls, data: Union[bytes, str], key: bytes, iv: bytes, encoding='UTF-8'):
        d: bytes = data if isinstance(data, bytes) else data.encode(encoding)
        d += b"\0"  # enforce the data to be non empty (because on some OS' crypto won't work without this trick)
        cls._check_key(key)
        _, d = aes_cbc_pkcs7_encrypt(key, d, iv)
        return (cls.magic + b85encode(d, True) + cls.magicend).decode(encoding)

    def str(self, encoding='UTF-8') -> str:
        return self.bytes().decode(encoding)

    def bytes(self) -> bytes:
        if self.data is _INVALID:
            raise Exception("no more valid")
        if self.encrypted:
            return self._decrypt(self.data, self._key, self._iv)
        return self.data

    def ensure_encrypted(self, encoding='UTF-8') -> 'EncryptedString':
        data = self.encrypt(self.str(encoding), self._key, self._iv, encoding)
        return EncryptedString(data, self._key, self._iv, encoding)

    def __enter__(self):
        if self.data is _INVALID:
            raise Exception("no more valid")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.data = _INVALID

    def __str__(self):
        return self.str()
