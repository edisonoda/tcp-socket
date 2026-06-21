from common import *

from socket import *
import os
import time
import threading
import hashlib

from datetime import datetime

SEG_SIZE = BUFFER_SIZE
ARQ_CHUNK = 8192

# Estruturas:
# - { 'IP:PORT': {...} }
CLIENTS = {}

# Cria o socket TCP (IPv4, Stream)
S_SOCKET = socket(AF_INET, SOCK_STREAM)

def formatted_client(addr):
    c_ip, c_port = addr
    return f'{c_ip}:{c_port}'

def handle_client(conn, addr):
    create_client(conn, addr)

    while True:
        msg = conn.recv(2048)
        handle_req(msg, conn)
    
    # remove_client(conn)
    # print(f'Cliente desconectado: {formatted_client(addr)}')
    # broadcast_message(f'{formatted_client(addr)} saiu da sala', except_conn=None)

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
            chunk = f.read(ARQ_CHUNK)
            if not chunk:
                break

            sha256.update(chunk)

            for i in range(0, len(chunk), SEG_SIZE):
                seg = chunk[i:i+SEG_SIZE]
                conn.send(f'DATA '.encode() + seg)
                print(f'Enviado: {min(i+SEG_SIZE, len(chunk))}/{len(chunk)} bytes do arquivo {filename}')

    conn.send(f'END '.encode() + sha256.hexdigest().encode())
    print(f'Arquivo {filename} enviado com sucesso! Hash: {sha256.hexdigest()}')

def start_transfer(filename, conn):
    if not filename:
        msg = f'ERROR 400: {filename} (nome do arquivo invalido)'
        print(msg)
        conn.send(msg.encode())
        return

    if filename[0] != '/':
        filename = '/' + filename
    
    if not os.path.isfile(FILE_DIR + filename):
        msg = f'ERROR 404: Arquivo {filename} nao encontrado!'
        print(msg)
        conn.send(msg.encode())
        return

    total = os.path.getsize(FILE_DIR + filename)

    print(f'Transferência iniciada para {CLIENTS[conn]["name"]}: {filename}')
    conn.send(f'START {total}'.encode())
    
    send_file(conn, filename)

def handle_req(msg, conn):
    action, args = parse_msg(msg)
    action = action.decode()
    args = [arg.decode() for arg in args]

    if action == 'GET':
        filename = args[0] if args else None
        start_transfer(filename, conn)

    # elif action == 'ACK':
    #     seq = int(args[0]) if args else None
    #     handle_ack(addr, seq)

    # elif action == 'NACK':
    #     seq = int(args[0]) if args else None
    #     handle_nack(addr, seq)

def accept_clients():
    while True:
        conn, addr = S_SOCKET.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

def main():
    S_SOCKET.bind((S_IP, S_PORT))
    S_SOCKET.listen()
    print(f'Servidor escutando no endereco: {S_IP}:{S_PORT}')

    accept_clients()

if __name__ == "__main__":
    main()