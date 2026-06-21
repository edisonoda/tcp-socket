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
        print(f'ERRO: hash final não confere (esperado {sha256}, obtido {SHA256.hexdigest()})')
        return

    SHA256 = hashlib.sha256()
    name, ext = FILENAME.split('.', 1)

    if ext:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}.{ext}'
    else:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}'

    with open(save_name, 'wb') as f:
        for seq in RECEIVED:
            f.write(seq)

def receive_segment(data):
    global SHA256
    SHA256.update(data)
    RECEIVED.append(data)
    print(f'[{datetime.now().time().isoformat()}] Recebido: {len(RECEIVED)}/{TOTAL_SEGS}')

def handle_server():
    while True:
        cmd, data = recv_frame(C_SOCKET)
        if cmd is None:
            print('Conexao encerrada pelo servidor.')
            break

        action, args = parse_msg(cmd)
        action = action.decode()

        print(f'[{datetime.now().time().isoformat()}] Resposta do servidor: {action}')

        if action == 'START':
            global TOTAL_SEGS
            TOTAL_SEGS = int(args[0].decode())
        elif action == 'DATA':
            receive_segment(data)
        elif action == 'ERROR':
            print(f'ERROR {" ".join(arg.decode() for arg in args)}')
        elif action == 'END':
            print('Finalizado!')
            write_file(data.decode())

    # FILENAME = name if name[0] == '/' else '/' + name

def main():
    C_SOCKET.connect(SERVER)

    threading.Thread(target=handle_server, args=()).start()

    try:
        while True:
            cmd = input('> ').strip()
            if not cmd:
                continue

            send_frame(C_SOCKET, cmd.encode())

            if cmd.upper() == 'SAIR':
                break
    except KeyboardInterrupt:
        send_frame(C_SOCKET, b'SAIR')
    finally:
        C_SOCKET.close()

if __name__ == "__main__":
    main()