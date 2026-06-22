from common import *
from socket import *
from datetime import datetime

import random
import threading
import hashlib

SERVER = (S_IP, S_PORT)

C_SOCKET = socket(AF_INET, SOCK_STREAM)

FILENAME = '/diagrama.jpg'

TOTAL_SEGS = 0

RECEIVED = []
SHA256 = hashlib.sha256()

def write_file(sha256):
    global SHA256

    if sha256 != SHA256.hexdigest():
        print(f'ERRO: hash final não confere (esperado {sha256}, obtido {SHA256.hexdigest()})\n> ', end='')
        return

    name, ext = FILENAME.split('.', 1)

    if ext:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}.{ext}'
    else:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}'

    with open(save_name, 'wb') as f:
        for seq in RECEIVED:
            f.write(seq)
    
    SHA256 = hashlib.sha256()
    RECEIVED.clear()
    print(f'Arquivo salvo como: {save_name} (hash final: {sha256})\n> ', end='')

def receive_segment(data):
    global SHA256
    SHA256.update(data)
    RECEIVED.append(data)

def handle_server():
    while True:
        cmd, data = recv_frame(C_SOCKET)
        if cmd is None:
            print('Conexao encerrada pelo servidor.')
            C_SOCKET.close()
            break

        action = cmd.decode().upper()

        if action == 'START':
            global TOTAL_SEGS
            TOTAL_SEGS = int(data.decode()) / BUFFER_SIZE
        elif action == 'DATA':
            receive_segment(data)
        elif action == 'ERROR':
            print(f'ERROR {data.decode()}\n> ', end='')
        elif action == 'CHAT':
            print(f'[{datetime.now().time().isoformat()}] {data.decode()}\n> ', end='')
        elif action == 'END':
            write_file(data.decode())

def main():
    C_SOCKET.connect(SERVER)

    threading.Thread(target=handle_server, args=()).start()

    print('Conectado ao servidor. Use os comandos: EXIT, GET <nome>, CHAT <mensagem>')

    try:
        while True:
            cmd = input('> ').strip()
            if not cmd:
                continue

            parts = cmd.split(" ", 1)
            action = parts[0].upper().encode()

            payload = (parts[1].encode() if len(parts) > 1 else b'')
            send_frame(C_SOCKET, action, payload)

            if cmd.upper() == 'EXIT':
                break
    except KeyboardInterrupt:
        send_frame(C_SOCKET, b'EXIT')

if __name__ == "__main__":
    main()