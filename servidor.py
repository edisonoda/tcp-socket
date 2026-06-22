from common import *

from socket import *
import os
import time
import threading
import hashlib

from datetime import datetime

SEG_SIZE = BUFFER_SIZE

# Estruturas:
# - { 'CONN': {...} }
CLIENTS = {}

# Cria o socket TCP (IPv4, Stream)
S_SOCKET = socket(AF_INET, SOCK_STREAM)

def formatted_client(addr):
    c_ip, c_port = addr
    return f'{c_ip}:{c_port}'

def handle_client(conn, addr):
    create_client(conn, addr)
    connected = True

    while connected:
        msg, _ = recv_frame(conn)
        if msg is None:
            break
        connected = handle_req(msg, conn)

    remove_client(conn)
    print(f'Cliente desconectado: {formatted_client(addr)}')

def create_client(conn, addr):
    CLIENTS[conn] = {
        'addr': addr,
        'name': formatted_client(addr),
        'filename': None
    }

    print(f'Cliente conectado: {formatted_client(addr)}')

def remove_client(conn):
    if conn in CLIENTS:
        CLIENTS.pop(conn)
    
    conn.close()

def send_file(conn, filename):
    sha256 = hashlib.sha256()
    
    with open(FILE_DIR + filename, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break

            sha256.update(chunk)
            send_frame(conn, b'DATA', chunk)

    send_frame(conn, b'END', sha256.hexdigest().encode())
    print(f'Arquivo {filename} enviado com sucesso! Hash: {sha256.hexdigest()}')

def start_transfer(filename, conn):
    if not filename:
        msg = f'ERROR 400: {filename} (nome do arquivo invalido)'
        print(msg)
        send_frame(conn, msg.encode())
        return
    
    if '\\..' in filename:
        msg = f'ERROR 403: {filename} (erro de permissao para acessar o arquivo)'
        print(msg)
        send_frame(conn, msg.encode())
        return

    if filename[0] != '/':
        filename = '/' + filename
    
    if not os.path.isfile(FILE_DIR + filename):
        msg = f'ERROR 404: Arquivo {filename} nao encontrado!'
        print(msg)
        send_frame(conn, msg.encode())
        return

    total = os.path.getsize(FILE_DIR + filename)

    print(f'Transferência iniciada para {CLIENTS[conn]["name"]}: {filename}')
    send_frame(conn, f'START {total}'.encode())
    
    send_file(conn, filename)

def handle_req(msg, conn):
    action, args = parse_msg(msg)
    action = action.decode().upper()
    args = [arg.decode() for arg in args]

    if action == 'EXIT':
        send_frame(conn, b'BYE')
        return False

    if action == 'GET':
        filename = args[0] if args else None
        start_transfer(filename, conn)
    
    return True

    # elif action == 'ACK':
    #     seq = int(args[0]) if args else None
    #     handle_ack(addr, seq)

    # elif action == 'NACK':
    #     seq = int(args[0]) if args else None
    #     handle_nack(addr, seq)

def broadcast_message(message):
    for conn, info in list(CLIENTS.items()):
        try:
            send_frame(conn, f'CHAT {message}'.encode())
        except Exception:
            remove_client(conn)

def accept_clients():
    while True:
        conn, addr = S_SOCKET.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

def server_broadcast():
    while True:
        message = input().strip()
        if message:
            broadcast_message(f'SERVER: {message}')

def main():
    S_SOCKET.bind((S_IP, S_PORT))
    S_SOCKET.listen()
    print(f'Servidor escutando no endereco: {S_IP}:{S_PORT}')

    threading.Thread(target=server_broadcast).start()
    accept_clients()

if __name__ == "__main__":
    main()