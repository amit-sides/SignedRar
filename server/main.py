import sys
import socket
import logging

import construct
import timeout_decorator

from common import messages
from server import server
from server import request_handler

CLIENT_TIMEOUT = 60  # Seconds

def configure_logging():
    logging.basicConfig(level=logging.INFO, datefmt="%d.%m.%Y %H:%M:%S",
                        format="%(asctime)-19s [%(levelname)-8s] %(funcName)-21s | %(message)s")

def send_reply(client_socket, code, owner_uuid):
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

@timeout_decorator.timeout(CLIENT_TIMEOUT)
def client_handler(client_socket, address):
    try:
        # Run the client handler
        handle_client(client_socket)
        logging.info(f"Finished serving client {address}")
    except timeout_decorator.TimeoutError as e:
        # Timeout occurred - Send Error Message
        logging.info(f"Timeout passed for client {address}")
        send_reply(client_socket, messages.ErrorCodes.TIMEOUT)
    finally:
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
            else:
                return_code = messages.ErrorCodes.INVALID_MESSAGE
        except construct.ConstructError:
            logging.error(f"Failed to parse message with length: {len(message)}", exc_info=True)
            return_code = messages.ErrorCodes.INVALID_MESSAGE

        send_reply(client_socket, return_code, owner_uuid)


def main():
    configure_logging()

    # Start the server
    logging.info(f"Starting server... port: {server.PORT}")
    request_handler.init()
    tls_server = server.TLSServer()
    tls_server.start_server()
    try:
        tls_server.serve_forever(client_handler)
    except KeyboardInterrupt:
        tls_server.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
