from common import *

from socket import *
import os
import time
import threading
from datetime import datetime

SEG_SIZE = BUFFER_SIZE

# Estruturas:
# - { 'filename': [seg0, seg1, ...] }
# - { 'IP:PORT': {...} }
FILES = {}
CLIENTS = {}

# Cria o socket TCP (IPv4, Stream)
S_SOCKET = socket(AF_INET, SOCK_STREAM)

def formatted_client(addr):
    c_ip, c_port = addr
    return f'{c_ip}:{c_port}'

def handle_client(conn, addr):
    create_client(conn, addr)

def create_client(conn, addr):
    CLIENTS[formatted_client(addr)] = {
        'addr': addr,
        'conn': conn,
        'filename': None
    }

    print(f'Cliente conectado: {formatted_client(addr)}')

def segment_file(filename):
    with open(FILE_DIR + filename, 'rb') as f:
        while True:
            seg = f.read(SEG_SIZE)
            if not seg:
                break
            yield seg

def start_transfer(filename, addr):
    if not filename:
        msg = f'ERROR 400: {filename} (nome do arquivo invalido)'
        print(msg)
        S_SOCKET.sendto(msg.encode(), addr)
        return

    if filename[0] != '/':
        filename = '/' + filename
    
    if not os.path.isfile(FILE_DIR + filename):
        msg = f'ERROR 404: Arquivo {filename} nao encontrado!'
        print(msg)
        S_SOCKET.sendto(msg.encode(), addr)
        return

    if filename not in FILES.keys():
        FILES[filename] = list(segment_file(filename))

    total = len(FILES[filename])

    print(f'Transferência iniciada para {formatted_client(addr)}: {filename}')
    S_SOCKET.sendto(f'START {total}'.encode(), addr)

    # Send

# def handle_req(msg, addr):
#     action, args = parse_msg(msg)
#     action = action.decode()
#     args = [arg.decode() for arg in args]

#     if action == 'GET':
#         filename = args[0] if args else None
#         start_transfer(filename, addr)

#     elif action == 'ACK':
#         seq = int(args[0]) if args else None
#         handle_ack(addr, seq)

#     elif action == 'NACK':
#         seq = int(args[0]) if args else None
#         handle_nack(addr, seq)

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