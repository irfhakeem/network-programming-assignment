from socket import *
import socket
import threading
import logging
import time
import sys
from datetime import datetime
from datetime import timezone, timedelta

logging.basicConfig(level=logging.INFO)

class ProcessTheClient(threading.Thread):
        def __init__(self, connection, address):
                self.connection = connection
                self.address = address
                threading.Thread.__init__(self)

        def run(self):
                while True:
                        data = self.connection.recv(128)
                        if not data:
                            break

                        message = data.decode('utf-8').strip()
                        logging.info(f"Received from {self.address}: {message}")

                        split_message = message.split()

                        if len(split_message) < 3:
                            continue

                        if (split_message[0] == "TIME" and split_message[-2] == "13" and split_message[-1] == "10") or (split_message[0] == "QUIT" and split_message[-2] == "13" and split_message[-1] == "10"):
                            tz = timezone(timedelta(hours=7))
                            curr_time = datetime.now(tz).strftime("%d %m %Y %H:%M:%S")
                            response = f"JAM {curr_time} 13 10\r\n"
                            self.connection.sendall(response.encode('utf-8'))

                        else:
                            continue

                self.connection.close()

class Server(threading.Thread):
        def __init__(self):
                self.the_clients = []
                self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                threading.Thread.__init__(self)

        def run(self):
                self.my_socket.bind(('0.0.0.0', 45000))
                self.my_socket.listen(1)
                while True:
                    self.connection, self.client_address = self.my_socket.accept()
                    logging.warning(f"connection from {self.client_address}")

                    clt = ProcessTheClient(self.connection, self.client_address)
                    clt.start()
                    self.the_clients.append(clt)


def main():
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()
