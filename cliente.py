from common import *
from socket import *
from datetime import datetime

import random

SERVER = (S_IP, S_PORT)

C_SOCKET = socket(AF_INET, SOCK_STREAM)

FILENAME = '/diagrama.jpg'

TOTAL_SEGS = 0

# Dict para receber fora de ordem/com perdas
RECEIVED = {}

def write_file():
    name, ext = FILENAME.split('.', 1)

    if ext:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}.{ext}'
    else:
        save_name = f'{FILE_DIR}{name}_recebido_{datetime.now().isoformat()}'

    with open(save_name, 'wb') as f:
        for seq in sorted(RECEIVED.keys()):
            f.write(RECEIVED[seq])

# Estrutura: DATA seq checksum bytes
def receive_segment(args):
    if len(args) < 3:
        print(f'[{datetime.now().time().isoformat()}] Erro (pacote truncado | argumentos insuficientes) no segmento {seq + 1}')
        C_SOCKET.sendto(f'NACK {seq}'.encode(), SERVER)
        return
    
    seq, cs = args[:2]
    seq = int(seq.decode())
    cs = cs.decode()

    data = args[2]

    if cs != checksum(data):
        print(f'[{datetime.now().time().isoformat()}] Erro (checksum) no segmento {seq + 1}')
        C_SOCKET.sendto(f'NACK {seq}'.encode(), SERVER)
    else:
        print(f'[{datetime.now().time().isoformat()}] Recebido: {seq + 1}/{TOTAL_SEGS}')
        RECEIVED[seq] = data
        C_SOCKET.sendto(f'ACK {seq}'.encode(), SERVER)

def handle_res(res, addr):
    action, args = parse_msg(res)
    action = action.decode()

    if action == 'START':
        global TOTAL_SEGS
        TOTAL_SEGS = int(args[0].decode())
    elif action == 'DATA':
        receive_segment(args)
    elif action == 'ERROR':
        print(f'ERROR {" ".join(arg.decode() for arg in args)}')
    elif action == 'END':
        print('Finalizado!')
        write_file()
        return True
    
    return False

    # FILENAME = name if name[0] == '/' else '/' + name

def main():
    C_SOCKET.connect(SERVER)
    end = False

    # while not end:

    # Encerra a conexão
    # C_SOCKET.close()

if __name__ == "__main__":
    main()