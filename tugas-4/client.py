import socket
import json
import base64
import multiprocessing
from multiprocessing import Pool
import logging

def send_request(request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('172.16.16.101', 8889)
    sock.connect(server_address)
    logging.warning(f"Connecting to {server_address}")

    sock.send(request.encode())
    response = sock.recv(4096)
    result = response.decode()
    sock.close()

    if '\r\n\r\n' in result:
        return result.split('\r\n\r\n', 1)[1]
    return result

def remote_upload_file(filename, content):
    json_data = {
        "filename": f"{filename}",
        "content": content,
    }

    json_payload = json.dumps(json_data)

    request = f"""POST /upload HTTP/1.0\r
Content-Type: application/json\r
Content-Length: {len(json_payload)}\r
\r
{json_payload}\r
"""
    return send_request(request)

def remote_delete_file(filename_path):
    request = f"""DELETE /{filename_path} HTTP/1.0\r
\r
"""
    return send_request(request)

def remote_get(endpoint):
    request = f"""GET {endpoint} HTTP/1.0\r
\r
"""
    return send_request(request)

def run_tasks(worker_id):
    tasks = [
        ("get", "/list/"),
        ("upload", f"test_file_worker_{worker_id}.txt", "SW5pIGZpbGUgdGVzdGluZyBoZWhl"),
        ("get", "/list/"),
        ("delete", f"test_file_worker_{worker_id}.txt"),
        ("get", "/list/"),
    ]

    res = []
    for i, (task_type, *args) in enumerate(tasks):
        if task_type == "upload":
            result = remote_upload_file(args[0], args[1])
        elif task_type == "delete":
            result = remote_delete_file(args[0])
        elif task_type == "get":
            result = remote_get(args[0])

        res.append(f"Worker {worker_id} - Task {i+1}:\n{result.strip()}\n")

    return res

if __name__ == "__main__":
    #  3 workers
    worker = 3
    w_id = list(range(1, worker + 1))

    with Pool(processes=worker) as pool:
        all_results = pool.map(run_tasks, w_id)

    # results
    for worker_results in all_results:
        for result in worker_results:
            print(result)
        print("-" * 50)
