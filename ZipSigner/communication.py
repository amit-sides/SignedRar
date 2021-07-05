import os
import socket
import ssl
import construct

from common import messages

CA_CERTIFICATE = os.path.join("ZipSigner", "ca.crt")
SERVER_IP = "localhost"
SERVER_PORT = 12345
CONTEXT = None


def init():
    global CONTEXT

    CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    CONTEXT.verify_mode = ssl.CERT_REQUIRED
    CONTEXT.load_verify_locations(CA_CERTIFICATE)
    CONTEXT.check_hostname = False


def handle_reply(reply):
    if len(reply) != messages.MESSAGE_SIZE:
        return messages.ErrorCodes.MESSAGE_INCORRECT_SIZE, None, \
               messages.ERROR_CODE_TO_MESSAGE[messages.ErrorCodes.MESSAGE_INCORRECT_SIZE]

    # Parse the message
    try:
        generic_message = messages.GENERIC_MESSAGE.parse(reply)
        if int(generic_message.type) == messages.MessageType.OK:
            ok_message = messages.OK_MESSAGE.parse(reply)
            return messages.ErrorCodes.OK, ok_message.owner_uuid, None
        elif int(generic_message.type) == messages.MessageType.ERROR:
            error_message = messages.ERROR_MESSAGE.parse(reply)
            return error_message.error_code, None, error_message.error_message
        else:
            return messages.ErrorCodes.INVALID_MESSAGE, None, \
                   messages.ERROR_CODE_TO_MESSAGE[messages.ErrorCodes.INVALID_MESSAGE]
    except construct.ConstructError:
        pass

    return messages.ErrorCodes.INVALID_MESSAGE, None, \
           messages.ERROR_CODE_TO_MESSAGE[messages.ErrorCodes.INVALID_MESSAGE]


def register_certificate(certificate):
    public_key = certificate.export_public().encode("utf-8")
    owner = certificate.owner.encode("utf-8")
    register_certificate_dict = dict(
        type=messages.MessageType.REGISTER_CERTIFICATE,
        owner=owner,
        owner_size=len(owner),
        public_key=public_key,
        public_key_size=len(public_key)
    )
    message = messages.REGISTER_CERTIFICATE_MESSAGE.build(register_certificate_dict)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            with CONTEXT.wrap_socket(client_socket) as tls_socket:
                tls_socket.connect((SERVER_IP, SERVER_PORT))
                tls_socket.send(message)
                reply = tls_socket.recv(messages.MESSAGE_SIZE)
                return handle_reply(reply)
    except (ssl.SSLError, ssl.SSLError, ConnectionRefusedError) as e:
        return_code = messages.ErrorCodes.COMMUNICATION_ERROR
        return_message = f"Unable to connect the server at '{SERVER_IP}:{SERVER_PORT}'".encode("utf-8")
        return return_code, None, return_message

def delete_certificate(certificate):
    private_key = certificate.key_pair.export_key()
    owner = certificate.owner.encode("utf-8")
    delete_certificate_dict = dict(
        type=messages.MessageType.DELETE_CERTIFICATE,
        owner_uuid=certificate.uuid.encode("utf-8"),
        owner=owner,
        owner_size=len(owner),
        private_key=private_key,
        private_key_size=len(private_key)
    )
    message = messages.DELETE_CERTIFICATE_MESSAGE.build(delete_certificate_dict)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            with CONTEXT.wrap_socket(client_socket) as tls_socket:
                tls_socket.connect((SERVER_IP, SERVER_PORT))
                tls_socket.send(message)
                reply = tls_socket.recv(messages.MESSAGE_SIZE)
                return handle_reply(reply)
    except (ssl.SSLError, ssl.SSLError, ConnectionRefusedError) as e:
        return_code = messages.ErrorCodes.COMMUNICATION_ERROR
        return_message = f"Unable to connect the server at '{SERVER_IP}:{SERVER_PORT}'".encode("utf-8")
        return return_code, None, return_message

def verify_certificate(certificate):
    public_key = certificate.key_pair.export_key()
    owner = certificate.owner.encode("utf-8")
    verify_certificate_dict = dict(
        type=messages.MessageType.VERIFY_CERTIFICATE,
        owner_uuid=certificate.uuid.encode("utf-8"),
        owner=owner,
        owner_size=len(owner),
        public_key=public_key,
        public_key_size=len(public_key)
    )
    message = messages.VERIFY_CERTIFICATE_MESSAGE.build(verify_certificate_dict)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            with CONTEXT.wrap_socket(client_socket) as tls_socket:
                tls_socket.connect((SERVER_IP, SERVER_PORT))
                tls_socket.send(message)
                reply = tls_socket.recv(messages.MESSAGE_SIZE)
                return handle_reply(reply)
    except (ssl.SSLError, ssl.SSLError, ConnectionRefusedError) as e:
        return_code = messages.ErrorCodes.COMMUNICATION_ERROR
        return_message = f"Unable to connect the server at '{SERVER_IP}:{SERVER_PORT}'".encode("utf-8")
        return return_code, None, return_message
