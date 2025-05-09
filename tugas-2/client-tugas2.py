import threading
import socket
import datetime

def worker(nomor):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('172.16.16.101', 45000))
            print(f"[Worker {nomor}] Connected")

            sock.sendall("TIME\r\n".encode('utf-8'))
            response = sock.recv(1024).decode('utf-8').strip()

            time = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[Worker {nomor} - {time}]: {response}")

            sock.sendall("QUIT\r\n".encode('utf-8'))
            print(f"[Worker {nomor}]: Disconnected")
    except Exception as e:
        print(f"[Worker {nomor}] Error: {e}")

threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)

for thr in threads:
    thr.start()

for thr in threads:
    thr.join()
