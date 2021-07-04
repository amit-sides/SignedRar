import sys
import logging


import server
import client_handler
import request_handler



def configure_logging():
    logging.basicConfig(level=logging.INFO, datefmt="%d.%m.%Y %H:%M:%S",
                        format="%(asctime)-19s [%(levelname)-8s] %(funcName)-21s | %(message)s")

def main():
    configure_logging()

    # Start the server
    logging.info(f"Starting server... port: {server.PORT}")
    request_handler.init()
    tls_server = server.TLSServer()
    tls_server.start_server()
    try:
        tls_server.serve_forever(client_handler.client_handler)
    except KeyboardInterrupt:
        tls_server.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
