import tempfile
import zipfile
import hashlib

import dirhash

from ZipSigner import certificate

class SignedZip(zipfile.ZipFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._certificate = None

    @property
    def _hash(self):
        with tempfile.TemporaryDirectory() as td:
            self.extractall(td)
            try:
                return dirhash.dirhash(td, "sha384").encode("utf-8")
            except ValueError as e:
                if "Nothing to hash" in e.args[0]:
                    return hashlib.sha384(b"").hexdigest()
                raise e

    @property
    def certificate(self):
        if self._certificate is None:
            _, self._certificate = self.parse_signature()
        return self._certificate

    def sign(self, certificate):
        signature = certificate.sign_hash(self._hash)
        comment = f"Owner: {certificate.owner}\n"
        comment += f"UUID: {certificate.uuid}\n"
        comment += f"Signature:\n{signature}\n\n"
        comment += f"Public Key:\n{certificate.export_public()}"
        self.comment = comment.encode("utf-8")

    def parse_signature(self):
        if not self.comment:
            return None, None

        lines = self.comment.decode("utf-8").splitlines()
        if len(lines) < 5:
            return None, None

        owner = lines[0][len("Owner: "):]
        uuid = lines[1][len("UUID: "):]
        signature = lines[3]
        public_key = '\n'.join(lines[6:])
        return signature, certificate.Certificate.from_pem(owner, public_key, uuid)

    def verify(self):
        signature, self._certificate = self.parse_signature()
        if signature is None or self._certificate is None:
            return False
        return self._certificate.validate_hash(self._hash, signature)
