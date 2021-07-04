import hashlib

from Crypto.PublicKey import RSA

def sign(data, private_key, n):
    hash_object =  hashlib.sha384(data)
    return sign_hash(hash_object, private_key, n)

def sign_hash(hash, private_key, n):
    if type(hash) is str:
        hash = hash.encode("utf-8")
    calculated_hash = int.from_bytes(hash, byteorder='big')
    signature = pow(calculated_hash, private_key, n)
    return signature

def validate(data, signature, public_key, n):
    hash_object = hashlib.sha384(data)
    return validate_hash(hash_object, signature, public_key, n)

def validate_hash(hash, signature, public_key, n):
    if type(hash) is str:
        hash = hash.encode("utf-8")
    calculated_hash = int.from_bytes(hash, byteorder='big')
    hash_from_signature = pow(signature, public_key, n)
    return calculated_hash == hash_from_signature

def keys_match(private_key_pem, public_key_pem):
    private_key = RSA.import_key(private_key_pem)
    public_key = RSA.import_key(public_key_pem)
    return private_key.e == public_key.e and private_key.n == public_key.n and private_key.has_private()
