from socket import *
import os
import time
import threading

from datetime import datetime

S_IP = '127.0.0.1'
S_PORT = 2000

FILE_DIR = 'html'
BUFFER_SIZE = 8192

CLIENTS = {}

S_SOCKET = socket(AF_INET, SOCK_STREAM)

def recv_http_request(conn):
    request = b''

    while not request.endswith(b'\r\n\r\n'):
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            return None
        
        request += chunk
    
    return request.decode()

def parse_http_request(request):
    lines = request.split('\r\n')

    if not lines:
        return None, None
    
    method, path, _ = lines[0].split(' ', 2)

    return method.upper(), path

def formatted_client(addr):
    c_ip, c_port = addr
    return f'{c_ip}:{c_port}'

def handle_client(conn, addr):
    create_client(conn, addr)
    connected = True

    while connected:
        req = recv_http_request(conn)
        if req is None:
            break

        method, path = parse_http_request(req)

        if method is None:
            break

        connected = handle_req(method, path, conn)

    remove_client(conn)
    print(f'Cliente desconectado: {formatted_client(addr)}')

def create_client(conn, addr):
    CLIENTS[conn] = {
        'addr': addr,
        'name': formatted_client(addr),
    }

    print(f'Cliente conectado: {formatted_client(addr)}')

def remove_client(conn):
    if conn in CLIENTS:
        CLIENTS.pop(conn)
    
    conn.close()

def send_header(conn, length, status_code, content_type='text/html'):
    conn.sendall(f'HTTP/1.1 {status_code}\r\n'
                 f'Content-Length: {length}\r\n'
                 f'Content-Type: {content_type}\r\n'
                 f'\r\n'.encode())

def send_file(conn, filename):
    name, ext = filename.split('.', 1)
    total = os.path.getsize(FILE_DIR + filename)
    
    match ext:
        case 'html':
            send_header(conn, total, '200 OK', content_type='text/html')
        case 'jpg' | 'jpeg':
            send_header(conn, total, '200 OK', content_type='image/jpeg')
        case 'png':
            send_header(conn, total, '200 OK', content_type='image/png')
        case _:
            send_header(conn, total, '200 OK', content_type='text/plain')

    with open(FILE_DIR + filename, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break

            conn.sendall(chunk)
    
    print(f'Arquivo {filename} enviado com sucesso!')

def start_transfer(filename, conn):
    if '\\..' in filename or '/..' in filename:
        send_file(conn, '/403.html')
        return
    
    if not filename:
        send_file(conn, '/400.html')
        return

    if filename[0] != '/':
        filename = '/' + filename
    
    if not os.path.isfile(FILE_DIR + filename):
        send_file(conn, '/404.html')
        return

    print(f'Transferência iniciada para {CLIENTS[conn]["name"]}: {filename}')
    send_file(conn, filename)

def handle_req(method, path, conn):
    action = method.upper()

    if action == 'GET':
        start_transfer(path, conn)
    
    return True

def accept_clients():
    try:
        while True:
            conn, addr = S_SOCKET.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        for conn in list(CLIENTS):
            remove_client(conn)
        
        S_SOCKET.close()

def main():
    S_SOCKET.bind((S_IP, S_PORT))
    S_SOCKET.listen()
    print(f'Servidor escutando no endereco: {S_IP}:{S_PORT}')

    accept_clients()

if __name__ == "__main__":
    main()