from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from file_protocol import FileProtocol
fp = FileProtocol()

def ProcessTheClient(connection):
    buff = ""
    try:
        data = connection.recv(256)
        req = data.decode().split()[0]

        """
        Untuk meningkatkan performance saat upload file, buffer size ditingkatkan
        dan split file_name dan buffer dilakukan di awal agar tidak perlu
        split pada protokol.
        """

        if req == "UPLOAD":
            file_name = data.decode().split()[1]
            buff = data.decode().split()[2]

            while True:
                # Increased buffer size menjadi 20MB dari 32 Bytes
                data = connection.recv(200 * 1024 * 1024)
                if data:
                    buff += data.decode()
                    if "\r\n" in buff:
                        hasil = fp.proses_string(req, file_name, buff)
                        hasil = hasil+"\r\n\r\n"
                        connection.sendall(hasil.encode())
                        buff = ""
                else:
                    break
        else:
            hasil = fp.proses_string(data.decode())
            hasil = hasil+"\r\n\r\n"
            connection.sendall(hasil.encode())
    except Exception as e:
        logging.warning(f"error during client processing: {e}")
    finally:
        connection.close()

# Kelas server utama
class Server:
    def __init__(self, ipaddress='0.0.0.0', port=8889):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(100)

        worker = 1
        # --- MODE MULTITHREADING ---
        with ThreadPoolExecutor(max_workers=worker) as thread_pool:
            print(f"Multithreading {worker} worker")
            try:
                while True:
                    connection, client_address = self.my_socket.accept()
                    logging.warning(f"connection from {client_address}")
                    thread_pool.submit(ProcessTheClient, connection)
            except KeyboardInterrupt:
                logging.warning("shutting down server")
            finally:
                self.my_socket.close()

        # --- MODE MULTIPROCESSING ---
        # with ProcessPoolExecutor(max_workers=worker) as process_pool:
        #     print(f"Multiprocessing {worker} worker")
        #     try:
        #         while True:
        #             connection, client_address = self.my_socket.accept()
        #             logging.warning(f"Connection from {client_address}")
        #             process_pool.submit(ProcessTheClient, connection)
        #     except KeyboardInterrupt:
        #         logging.warning("Server dimatikan dengan KeyboardInterrupt")
        #     finally:
        #         self.my_socket.close()

def main():
    svr = Server(ipaddress='0.0.0.0', port=7777)
    svr.start()

if __name__ == "__main__":
    main()
