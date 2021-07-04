import os
import json
import logging
import uuid

import construct

from common import messages
from common import rsa

CA_DATABASE = os.path.join("server", "certificates.json")
UUID_TO_CERTIFICATE = dict()

def init():
    global UUID_TO_CERTIFICATE

    if os.path.exists(CA_DATABASE) and os.path.isfile(CA_DATABASE):
        with open(CA_DATABASE, "r") as db:
            UUID_TO_CERTIFICATE = json.loads(db.read())


def verify_certificate(message):
    # Parse the message
    try:
        message = messages.VERIFY_CERTIFICATE_MESSAGE.parse(message)
    except construct.ConstructError:
        # Should never occur
        logging.critical(f"Failed to parse verify certificate message: {message.hex()}", exc_info=True)
        return messages.ErrorCodes.INVALID_MESSAGE, None

    # Validate certificate
    if message.owner_uuid not in UUID_TO_CERTIFICATE:
        return messages.ErrorCodes.UNKNOWN_CERTIFICATE, None

    certificate = UUID_TO_CERTIFICATE[message.owner_uuid]
    if message.owner != certificate[0] or message.public_key != certificate[1]:
        return messages.ErrorCodes.INVALID_CERTIFICATE, None

    return messages.ErrorCodes.OK, message.owner_uuid


def register_certificate(message):
    global UUID_TO_CERTIFICATE

    # Parse the message
    try:
        message = messages.REGISTER_CERTIFICATE_MESSAGE.parse(message)
    except construct.ConstructError:
        # Should never occur
        logging.critical(f"Failed to parse register certificate message: {message.hex()}", exc_info=True)
        return messages.ErrorCodes.INVALID_MESSAGE, None

    # Check if the public key already exists
    for k, v in UUID_TO_CERTIFICATE.items():
        public_key = v[1]
        if public_key == message.public_key:
            return messages.ErrorCodes.PUBLIC_KEY_ALREADY_USED, None

    # Generate UUID for the certificate owner
    owner_uuid = uuid.uuid4().hex
    while owner_uuid in UUID_TO_CERTIFICATE:
        owner_uuid = uuid.uuid4().hex

    # Add the certificate to the database
    UUID_TO_CERTIFICATE[owner_uuid] = (message.owner.decode('utf-8'), message.public_key.decode('utf-8'))
    with open(CA_DATABASE, "w") as db:
        json.dump(UUID_TO_CERTIFICATE, db)

    # Return OK message to client
    return messages.ErrorCodes.OK, owner_uuid

def delete_certificate(message):
    global UUID_TO_CERTIFICATE

    # Parse the message
    try:
        message = messages.DELETE_CERTIFICATE_MESSAGE.parse(message)
    except construct.ConstructError:
        # Should never occur
        logging.critical(f"Failed to parse delete certificate message: {message.hex()}", exc_info=True)
        return messages.ErrorCodes.INVALID_MESSAGE, None

    # Check that the certificate exists
    owner_uuid = message.owner_uuid.decode("utf-8")
    if owner_uuid not in UUID_TO_CERTIFICATE:
        return messages.ErrorCodes.UNKNOWN_CERTIFICATE, None

    certificate = UUID_TO_CERTIFICATE[owner_uuid]
    if message.owner.decode("utf-8") != certificate[0]:
        return messages.ErrorCodes.INVALID_CERTIFICATE, None

    if not rsa.keys_match(message.private_key, certificate[1]):
        return messages.ErrorCodes.INVALID_CERTIFICATE, None

    # Remove the certificate from the database
    del UUID_TO_CERTIFICATE[owner_uuid]
    with open(CA_DATABASE, "w") as db:
        json.dump(UUID_TO_CERTIFICATE, db)

    # Return OK message to client
    return messages.ErrorCodes.OK, message.owner_uuid




