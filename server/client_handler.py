import socket
import logging

import construct

from common import messages
import request_handler

CLIENT_TIMEOUT = 60  # Seconds


def send_reply(client_socket, code, owner_uuid):
    if type(owner_uuid) is str:
        owner_uuid = owner_uuid.encode("utf-8")
    if code == messages.ErrorCodes.OK:
        ok_message_dict = dict(
            type=messages.MessageType.OK,
            owner_uuid=owner_uuid,
        )
        message = messages.OK_MESSAGE.build(ok_message_dict)
    else:
        error_message_dict = dict(
            type=messages.MessageType.ERROR,
            error_code=code,
            error_message_size=len(messages.ERROR_CODE_TO_MESSAGE[code]),
            error_message=messages.ERROR_CODE_TO_MESSAGE[code],
        )
        message = messages.ERROR_MESSAGE.build(error_message_dict)
    client_socket.send(message)

def client_handler(client_socket, address):
    # Run the client handler
    handle_client(client_socket)
    logging.info(f"Finished serving client {address}")

    # Clean all resources
    client_socket.close()

def handle_client(client_socket):
    message = "a"
    while len(message) > 0:
        return_code = messages.ErrorCodes.OK
        owner_uuid = None

        # Get message and check size
        try:
            message = client_socket.recv(messages.MESSAGE_SIZE)
            if len(message) == 0:
                continue
            if len(message) != messages.MESSAGE_SIZE:
                logging.info(f"Received message with incorrect size: received {len(message)} expected {messages.MESSAGE_SIZE}")
                return_code = messages.ErrorCodes.MESSAGE_INCORRECT_SIZE
        except socket.error:
            logging.info("Failed to receive message from client. The message is probably too long.")
            return_code = messages.ErrorCodes.MESSAGE_INCORRECT_SIZE

        if return_code != messages.ErrorCodes.OK:
            send_reply(client_socket, return_code, owner_uuid)
            continue

        # Parse the message
        try:
            generic_message = messages.GENERIC_MESSAGE.parse(message)
            if int(generic_message.type) == messages.MessageType.VERIFY_CERTIFICATE:
                return_code, owner_uuid = request_handler.verify_certificate(message)
            elif int(generic_message.type) == messages.MessageType.REGISTER_CERTIFICATE:
                return_code, owner_uuid = request_handler.register_certificate(message)
            elif int(generic_message.type) == messages.MessageType.DELETE_CERTIFICATE:
                return_code, owner_uuid = request_handler.delete_certificate(message)
            else:
                return_code = messages.ErrorCodes.INVALID_MESSAGE
        except construct.ConstructError:
            logging.error(f"Failed to parse message with length: {len(message)}", exc_info=True)
            return_code = messages.ErrorCodes.INVALID_MESSAGE

        send_reply(client_socket, return_code, owner_uuid)
