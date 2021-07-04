from Crypto.PublicKey import RSA

from common import messages
from common import rsa
import communication

class Certificate(object):
    def __init__(self, owner, key_pair, uuid=None):
        self.owner = owner
        self.key_pair = key_pair
        self.uuid = uuid

    @staticmethod
    def from_pem(owner, key_pem, uuid=None):
        key_pair = RSA.import_key(key_pem)
        return Certificate(owner, key_pair, uuid)

    @staticmethod
    def generate(owner):
        key_pair = RSA.generate(bits=2048)
        return Certificate(owner, key_pair)

    def sign(self, data):
        if not self.key_pair.has_private():
            raise NotImplementedError("Unable to sign without private key!")
        return rsa.sign(data, self.key_pair.d, self.key_pair.n)

    def sign_hash(self, hash):
        if not self.key_pair.has_private():
            raise NotImplementedError("Unable to sign without private key!")
        return rsa.sign_hash(hash, self.key_pair.d, self.key_pair.n)

    def validate(self, data, signature):
        return rsa.validate(data, signature, self.key_pair.e, self.key_pair.n)

    def validate_hash(self, hash, signature):
        return rsa.validate_hash(hash, signature, self.key_pair.e, self.key_pair.n)

    def export_public(self):
        return self.key_pair.publickey().export_key().decode("utf-8")

    def register(self):
        return_code, response, error_message = communication.register_certificate(self)
        if return_code == messages.ErrorCodes.OK:
            self.uuid = response.decode("utf-8")
            return True, None
        return False, (return_code, error_message)

    def to_dict(self):
        return dict(
            owner=self.owner,
            uuid=self.uuid,
            key_pair=self.key_pair.export_key().decode("utf-8")
        )

    @staticmethod
    def from_dict(d):
        key_pair = RSA.import_key(d["key_pair"])
        return Certificate(d["owner"], key_pair, d["uuid"])

    def __str__(self):
        return f"{self.owner}-{self.uuid}"

