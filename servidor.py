from common import *

from socket import *
import os
import time
from datetime import datetime

SEG_SIZE = 1024

# Estruturas:
# - { 'filename': [seg0, seg1, ...] }
# - { 'IP:PORT': {...} }
FILES = {}
CLIENTS = {}

# Cria o socket UDP (IPv4, Datagrama)
S_SOCKET = socket(AF_INET, SOCK_DGRAM)

def segment_file(filename):
    with open(FILE_DIR + filename, 'rb') as f:
        while True:
            seg = f.read(SEG_SIZE)
            if not seg:
                break
            yield seg

def formatted_client(addr):
    c_ip, c_port = addr
    return f'{c_ip}:{c_port}'

def create_client(filename, addr):
    CLIENTS[formatted_client(addr)] = {
        'addr': addr,
        'filename': filename,
        'acked': set(),
        'sent_times': {},
        'seq': 0,
        'wnd_start': 0,
        'wnd_size': WND_SIZE
    }

def send_window(addr):
    client = CLIENTS[formatted_client(addr)]
    filename = client['filename']
    total = len(FILES[filename])

    while (client['seq'] < total and client['seq'] < client['wnd_start'] + client['wnd_size']):
        seq = client['seq']
        send_segment(filename, seq, addr)

        client['sent_times'][seq] = datetime.now().timestamp()
        client['seq'] += 1
    
    if len(client['acked']) == total:
        print(f'Transferência finalizada para {formatted_client(addr)}: {filename}')
        S_SOCKET.sendto(b'END', addr)

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

    # Caso o arquivo não tenha sido segmentado
    if filename not in FILES.keys():
        FILES[filename] = list(segment_file(filename))

    total = len(FILES[filename])

    print(f'Transferência iniciada para {formatted_client(addr)}: {filename}')
    S_SOCKET.sendto(f'START {total}'.encode(), addr)

    create_client(filename, addr)
    send_window(addr)

def send_segment(filename, seq, addr):
    data = FILES[filename][seq]
    cs = checksum(data)

    header = f'DATA {seq} {cs} '.encode()

    print(f'[{datetime.now().time().isoformat()}] Enviando {seq + 1}/{len(FILES[filename])} para {formatted_client(addr)}')
    S_SOCKET.sendto(header + data, addr)

def handle_ack(addr, seq):
    client = CLIENTS[formatted_client(addr)]
    if not client: return
    
    client['acked'].add(seq)
    while client['wnd_start'] in client['acked']:
        client['wnd_start'] += 1
    
    send_window(addr)

def handle_nack(addr, seq):
    client = CLIENTS[formatted_client(addr)]

    if client:
        print(f'NACK recebido para o pacote {seq + 1} de {formatted_client(addr)}')
        send_segment(client['filename'], seq, addr)
        client['sent_times'][seq] = datetime.now().timestamp()

# Protocolo simples para receber a requisição
def handle_req(msg, addr):
    action, args = parse_msg(msg)
    action = action.decode()
    args = [arg.decode() for arg in args]

    if action == 'GET':
        filename = args[0] if args else None
        start_transfer(filename, addr)

    elif action == 'ACK':
        seq = int(args[0]) if args else None
        handle_ack(addr, seq)

    elif action == 'NACK':
        seq = int(args[0]) if args else None
        handle_nack(addr, seq)

def check_timeouts():
    now = datetime.now().timestamp()

    for addr, client in CLIENTS.items():
        for seq in range(client['wnd_start'], client['seq']):
            if seq not in client['acked']:
                if now - client['sent_times'].get(seq, 0) > TIMEOUT:
                    print(f"!!! [{datetime.now().time().isoformat()}] Timeout {seq + 1} para {addr}")
                    send_segment(client['filename'], seq, client['addr'])
                    client['sent_times'][seq] = now

def main():
    S_SOCKET.bind((S_IP, S_PORT))
    print(f'Servidor escutando no endereco: {S_IP}:{S_PORT}')

    # Configuração de timeout do socket (para a verificação dos pacotes perdidos)
    S_SOCKET.settimeout(TIMEOUT / 2)

    while True:
        # Aguardar conexões/mensagens de clientes.
        # Bloqueia e aguarda pacote. Salva dados e IP/Porta de origem
        try:
            msg, addr = S_SOCKET.recvfrom(2048)
            handle_req(msg, addr)
        except timeout:
            pass

        check_timeouts()

if __name__ == "__main__":
    main()