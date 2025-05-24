import socket
import json
import base64
import logging
import os
import multiprocessing
import time
import pandas as pd

server_address=('0.0.0.0',7777)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            # Increase buffer size menjadi 10MB dari 16 Bytes
            data = sock.recv(10 * 1024 * 1024)
            if data:
                #data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = json.loads(data_received)
        return hasil
    except:
        logging.warning("error during data receiving")
        return False


def remote_list():
    command_str=f"LIST\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str=f"GET {filename}\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        #proses file dalam bentuk base64 ke bentuk bytes
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False

# New Protocol
def remote_upload(filename="", newfilename=""):
    files_dir = os.path.join(os.getcwd(), 'files', filename)

    if not os.path.exists(files_dir):
        print(f"File tidak ditemukan: {filename}")
        return False

    with open(files_dir, 'rb') as file:
        isifile = file.read()
        buff = base64.b64encode(isifile).decode('utf-8')

    command_str = f"UPLOAD {newfilename} {buff}\r\n"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        return True
    else:
        print("Gagal")
        return False

def remote_delete(filename=""):
    command_str=f"DELETE {filename}\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        return True
    else:
        print("Gagal")
        return False

def remote_download(filename="", newfilename=""):
    command_str=f"DOWNLOAD {filename}\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        files_dir = os.path.join(os.getcwd(), 'files')
        os.makedirs(files_dir, exist_ok=True)

        if not newfilename:
            newfilename = "download" + hasil['data_namafile']
        file_path = os.path.join(files_dir, newfilename)

        isifile = base64.b64decode(hasil['data_file'])
        with open(file_path, 'wb') as fp:
            fp.write(isifile)
            return True
    else:
        print("Gagal")
        return False

# Worker
def upload_worker(parameters):
    filename, new_filename = parameters
    start = time.time()
    try:
        success = remote_upload(filename, new_filename)
        size = os.path.getsize(os.path.join(os.getcwd(), 'files', filename)) if success else 0
    except Exception as e:
        logging.warning(f"Upload error: {e}")
        success = False
        size = 0
    end = time.time()
    return {"duration": end - start, "size": size, "success": success}

def download_worker(parameters):
    filename, new_filename = parameters
    start = time.time()
    try:
        success = remote_download(filename, new_filename)
        size = os.path.getsize(os.path.join(os.getcwd(), 'files', new_filename)) if success else 0
    except Exception as e:
        logging.warning(f"Download error: {e}")
        success = False
        size = 0
    end = time.time()
    return {"duration": end - start, "size": size, "success": success}

# Eksekusi tes
def stress_test(operation, file_size, num_clients):
    results = []

    if operation == "upload":
        filenames = [f"{file_size}MB.txt" for _ in range(num_clients)]
        parameters = [(filename, f"upload_{file_size}MB.txt") for filename in filenames]
        pool = multiprocessing.Pool(processes=num_clients)
        results = pool.map(upload_worker, parameters)
        pool.close()
        pool.join()

    else:
        pool = multiprocessing.Pool(processes=num_clients)
        filenames = [f"upload_{file_size}MB.txt" for _ in range(num_clients)]
        parameters = [(filename, f"download_{file_size}MB.txt") for filename in filenames]
        results = pool.map(download_worker, parameters)
        pool.close()
        pool.join()
    return results

def save_results(operation, file_size, num_clients, num_servers, results):
    csv_dir = os.path.join(os.getcwd(), 'log_ets_progjar.csv')

    if not os.path.exists(csv_dir):
        df = pd.DataFrame(columns=['operation', 'file_size', 'num_clients','num_servers',                                 'total_time', 'total_bytes', 'throughput', 'success', 'fail'])
    else:
        df = pd.read_csv(csv_dir)

    total_time = sum(r["duration"] for r in results)
    total_bytes = sum(r["size"] for r in results if r["success"])
    throughput = total_bytes / total_time if total_time > 0 else 0
    success = sum(1 for r in results if r["success"])
    fail = num_clients - success

    new_row = {
        'operation': operation,
        'file_size': file_size,
        'num_clients': num_clients,
        'num_servers': num_servers,
        'total_time': round(total_time, 2),
        'total_bytes': total_bytes,
        'throughput': round(throughput, 2),
        'success': success,
        'fail': fail
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(csv_dir, index=False)

# Main
if __name__ == "__main__":
    server_address=('172.16.16.101',7777)

    operations = ['upload', 'download']
    file_sizes = [10, 50, 100] #10 50 100
    client_workers = [1, 5, 50] #1 5 50
    server_workers = 1

    for op in operations:
        for size in file_sizes:
            for num in client_workers:
                print(f"Running: {op} - {size}MB - {num} Clients")
                results = stress_test(op, size, num)
                save_results(op, size, num, server_workers, results)
