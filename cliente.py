from common import *
from socket import *
from datetime import datetime

import random

SERVER = (S_IP, S_PORT)

# Cria o socket UDP (IPv4, Datagrama)
# AF_INET (Address Family - Internet)
# SOCK_DGRAM (Socket Datagram)
C_SOCKET = socket(AF_INET, SOCK_DGRAM)

FILENAME = '/diagrama.jpg'

TOTAL_SEGS = 0

LOSS_PROB = 0.05

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

def check_package_loss(seq):
    if random.random() < LOSS_PROB:
        print(f'!!! [{datetime.now().time().isoformat()}] Pacote {seq + 1} perdido')
        return True
    return False

# Estrutura: DATA seq checksum bytes
def receive_segment(args):
    if len(args) < 3:
        print(f'[{datetime.now().time().isoformat()}] Erro (pacote truncado | argumentos insuficientes) no segmento {seq + 1}')
        C_SOCKET.sendto(f'NACK {seq}'.encode(), SERVER)
        return
    
    seq, cs = args[:2]
    seq = int(seq.decode())
    cs = cs.decode()

    if check_package_loss(seq): return
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

def get_user_req():
    global FILENAME
    global LOSS_PROB
    global SERVER

    LOSS_PROB = float(input(f'Insira a probabilidade de perda de pacotes [Padrão: {LOSS_PROB}]: ') or LOSS_PROB)

    req = f'{S_IP}:{S_PORT}{FILENAME}'
    valid = False
    while not valid:
        req = input(f'Insira uma requisição no formato IP_Servidor:Porta_Servidor/nome_do_arquivo.ext [Padrão: {req}]:') or req

        ip, req = req.split(f':', 1)
        port, name = req.split(f'/', 1)

        if ip and port and port.isdigit() and name:
            valid = True

    SERVER = (ip, int(port))
    FILENAME = name if name[0] == '/' else '/' + name

def main():
    get_user_req()
    msg = f'GET {FILENAME}'

    # Configuração de timeout do socket (para a verificação de conexão com o servidor)
    C_SOCKET.settimeout(TIMEOUT * 10)
    confirmed_connection = False

    C_SOCKET.sendto(msg.encode(), SERVER)
    end = False

    while not end:
        # Aguarda resposta (buffer de 2048) e decodifica
        try:
            res, addr = C_SOCKET.recvfrom(2048)
            confirmed_connection = True
            end = handle_res(res, addr)
        except timeout:
            if not confirmed_connection:
                print(f'Erro: Não foi possível iniciar conexão com o servidor {S_IP}:{S_PORT} (timeout)')
            else:
                print(f'Erro: Conexão com o servidor {S_IP}:{S_PORT} perdida (timeout)')
            
            end = True

    # Encerra a conexão
    C_SOCKET.close()

if __name__ == "__main__":
    main()