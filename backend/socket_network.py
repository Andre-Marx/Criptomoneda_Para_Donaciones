import json
import socket
import threading
import time


class SocketNetwork:
    """
    Red local por sockets TCP con protocolo JSON por linea.
    El nodo servidor actua como punto de encuentro para los peers de la red WiFi.
    """

    def __init__(self, node_id, on_message=None, mode='server', host='0.0.0.0', port=7000, root_host='127.0.0.1', root_port=7000):
        self.node_id = node_id
        self.on_message = on_message
        self.mode = mode
        self.host = host
        self.port = port
        self.root_host = root_host
        self.root_port = root_port
        self.server_socket = None
        self.root_socket = None
        self.clients = {}
        self.peers = {}
        self.lock = threading.Lock()
        self.started = False

    def start(self):
        if self.started:
            return

        self.started = True

        if self.mode == 'peer':
            threading.Thread(target=self._connect_to_root, daemon=True).start()
        else:
            threading.Thread(target=self._start_server, daemon=True).start()

    def status(self):
        with self.lock:
            peers = list(self.peers.values())
            unique_peer_ids = {
                peer.get('node_id') or peer.get('peer_id')
                for peer in peers
            }

        return {
            'node_id': self.node_id,
            'mode': self.mode,
            'host': self.host,
            'port': self.port,
            'root_host': self.root_host,
            'root_port': self.root_port,
            'connected': self.mode == 'server' or self.root_socket is not None,
            'peer_count': len(unique_peer_ids),
            'connection_count': len(peers),
            'peers': peers
        }

    def broadcast(self, message):
        payload = {
            **message,
            'origin_node_id': message.get('origin_node_id', self.node_id),
            'sent_at': time.time()
        }

        if self.mode == 'peer':
            self._send_to_root(payload)
            return

        self._broadcast_to_clients(payload)

    def _start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(8)
        print(f'\n -- Red P2P escuchando en {self.host}:{self.port}')

        while True:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True).start()
            except OSError as e:
                print(f'\n -- Servidor P2P detenido o socket invalido: {e}')
                break

    def _connect_to_root(self):
        while True:
            root_socket = None

            try:
                root_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                root_socket.connect((self.root_host, self.root_port))
                self.root_socket = root_socket
                self._send_line(root_socket, {
                    'type': 'HELLO',
                    'node_id': self.node_id,
                    'mode': self.mode
                })
                self._send_line(root_socket, {
                    'type': 'SYNC_REQUEST',
                    'node_id': self.node_id,
                    'origin_node_id': self.node_id
                })
                print(f'\n -- Conectado al nodo raiz P2P {self.root_host}:{self.root_port}')
                self._listen(root_socket)
            except OSError as e:
                print(f'\n -- No se pudo conectar al nodo raiz P2P: {e}')
            finally:
                if self.root_socket is root_socket:
                    self.root_socket = None

                self._close_socket(root_socket)
                time.sleep(3)

    def _handle_client(self, client_socket, address):
        peer_id = f'{address[0]}:{address[1]}'

        with self.lock:
            self.clients[peer_id] = client_socket
            self.peers[peer_id] = {
                'peer_id': peer_id,
                'node_id': peer_id,
                'address': address[0],
                'port': address[1],
                'connected_at': time.time()
            }

        self._listen(client_socket, peer_id)
        self._drop_client(peer_id, client_socket)

    def _listen(self, source_socket, peer_id=None):
        buffer = ''

        while True:
            try:
                chunk = source_socket.recv(65536)
            except OSError as e:
                if peer_id:
                    print(f'\n -- Peer P2P desconectado ({peer_id}): {e}')
                break

            if not chunk:
                break

            buffer += chunk.decode('utf-8')

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f'\n -- Mensaje P2P invalido ignorado: {e}')
                    continue

                if message.get('type') == 'HELLO':
                    self._register_hello(peer_id, message)
                    continue

                if self.on_message:
                    self.on_message(message, peer_id=peer_id)

                if self.mode == 'server':
                    self._broadcast_to_clients(message, exclude_peer_id=peer_id)

    def _register_hello(self, peer_id, message):
        if not peer_id:
            return

        with self.lock:
            current = self.peers.get(peer_id, {})
            self.peers[peer_id] = {
                **current,
                'node_id': message.get('node_id', peer_id),
                'mode': message.get('mode', 'peer')
            }

    def send_to_peer(self, peer_id, message):
        with self.lock:
            client_socket = self.clients.get(peer_id)

        if not client_socket:
            return

        try:
            self._send_line(client_socket, {
                **message,
                'origin_node_id': message.get('origin_node_id', self.node_id),
                'sent_at': time.time()
            })
        except OSError:
            self._drop_client(peer_id, client_socket)

    def _broadcast_to_clients(self, message, exclude_peer_id=None):
        with self.lock:
            clients = list(self.clients.items())

        for peer_id, client_socket in clients:
            if peer_id == exclude_peer_id:
                continue

            try:
                self._send_line(client_socket, message)
            except OSError:
                self._drop_client(peer_id, client_socket)

    def _send_to_root(self, message):
        if not self.root_socket:
            return

        try:
            self._send_line(self.root_socket, message)
        except OSError:
            self._close_socket(self.root_socket)
            self.root_socket = None

    def _send_line(self, destination_socket, message):
        destination_socket.sendall((json.dumps(message) + '\n').encode('utf-8'))

    def _drop_client(self, peer_id, client_socket):
        with self.lock:
            if self.clients.get(peer_id) is client_socket:
                self.clients.pop(peer_id, None)

            self.peers.pop(peer_id, None)

        self._close_socket(client_socket)

    def _close_socket(self, target_socket):
        if not target_socket:
            return

        try:
            target_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            target_socket.close()
        except OSError:
            pass


def get_lan_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(('8.8.8.8', 80))
        ip = probe.getsockname()[0]
        probe.close()
        return ip
    except OSError:
        return '127.0.0.1'
