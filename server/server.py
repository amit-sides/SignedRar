import os
import logging
import socket
import multiprocessing as mp
import multiprocessing.dummy as multiprocessing
import ssl

CERTFILE = os.path.join("server", "certificates", "server.crt")
KEYFILE = os.path.join("server", "certificates", "server.key")
PORT = 12345
MAX_LISTENERS = 10

class TLSServer(object):
    def __init__(self):
        # Creating the TLS context
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        # Loading the server's certificate
        self.context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
        # Setting allowed protocols: ONLY TLS 1.3 ALLOWED!
        self.context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | \
                                ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2

        self.pool = multiprocessing.Pool()
        self.socket = None
        self.server = None
        self.running = False

    def start_server(self):
        # Start TLS server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("0.0.0.0", PORT))
        self.socket.listen(MAX_LISTENERS)

        # Wrap the listening TCP socket with the TLS connection
        self.server = self.context.wrap_socket(self.socket, server_side=True)
        self.server.settimeout(1.0)

        # Set server to running
        self.running = True

    def serve_forever(self, client_handler, *args, **kwargs):
        while True:
            try:
                conn, addr = self.server.accept()
            except (OSError, ConnectionError) as e:
                if e.args[0] != "timed out":
                    logging.error("Failed to accept a client: {}".format(e.args))
            else:
                try:
                    process = self.pool.Process(target=client_handler, args=(conn, addr) + args, kwargs=kwargs)
                except TypeError:  # In python 3.8+ The Process function requires additional parameter called `ctx`
                    ctx = mp.get_context()
                    #import ipdb; ipdb.set_trace()
                    process = self.pool.Process(ctx, target=client_handler, args=(conn, addr) + args, kwargs=kwargs)
                process.start()

    def close(self):
        self.pool.close()
        self.__del__()

    def __del__(self):
        self.pool.terminate()
        self.pool.join()
