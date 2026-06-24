import json
import socket
import threading
import time


P2P_PROTOCOL_VERSION = 3
HANDSHAKE_TIMEOUT_SECONDS = 12
HANDSHAKE_RETRY_SECONDS = 2


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
        self.root_lock = threading.Lock()
        self.write_locks = {}
        self.write_locks_lock = threading.Lock()
        self.started = False

    def start(self):
        if self.started:
            return

        self.started = True
        print(
            f'\n -- P2P protocolo v{P2P_PROTOCOL_VERSION} iniciado en modo {self.mode} '
            f'(codigo: {__file__})',
            flush=True
        )

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

        with self.root_lock:
            root_socket = self.root_socket

        return {
            'node_id': self.node_id,
            'mode': self.mode,
            'host': self.host,
            'port': self.port,
            'root_host': self.root_host,
            'root_port': self.root_port,
            'protocol_version': P2P_PROTOCOL_VERSION,
            'connected': self.mode == 'server' or root_socket is not None,
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
        print(f'\n -- Red P2P escuchando en {self.host}:{self.port}', flush=True)

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
                self._enable_tcp_low_latency(root_socket)
                self._set_socket_timeout(root_socket, 10)
                root_socket.connect((self.root_host, self.root_port))

                self._set_socket_timeout(root_socket, HANDSHAKE_RETRY_SECONDS)
                self._send_line(root_socket, self._hello_payload())
                pending_buffer = self._wait_for_hello_ack(root_socket)
                self._set_socket_timeout(root_socket, None)

                with self.root_lock:
                    self.root_socket = root_socket

                print(f'\n -- Conectado y registrado en nodo raiz P2P {self.root_host}:{self.root_port}', flush=True)
                self._listen(root_socket, initial_buffer=pending_buffer)
            except (OSError, TimeoutError) as e:
                print(f'\n -- No se pudo conectar al nodo raiz P2P: {e}', flush=True)
            finally:
                with self.root_lock:
                    if self.root_socket is root_socket:
                        self.root_socket = None

                self._close_socket(root_socket)
                time.sleep(3)

    def _handle_client(self, client_socket, address):
        peer_id = f'{address[0]}:{address[1]}'
        self._enable_tcp_low_latency(client_socket)
        self._set_socket_timeout(client_socket, HANDSHAKE_RETRY_SECONDS)
        print(f'\n -- Conexion P2P entrante desde {peer_id}; esperando HELLO...', flush=True)

        try:
            self._listen(client_socket, peer_id, address)
        finally:
            self._drop_client(peer_id, client_socket)

    def _listen(self, source_socket, peer_id=None, address=None, initial_buffer=''):
        buffer = initial_buffer
        handshake_deadline = time.time() + HANDSHAKE_TIMEOUT_SECONDS if peer_id else None
        last_hello_request_at = 0

        while True:
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                self._handle_line(line, source_socket, peer_id, address)

            try:
                chunk = source_socket.recv(65536)
            except socket.timeout:
                if peer_id and not self._is_active_peer_socket(peer_id, source_socket):
                    now = time.time()

                    if now >= handshake_deadline:
                        print(
                            f'\n -- No se recibio HELLO de {peer_id}; cerrando conexion P2P. '
                            'Verifica que el peer muestre "P2P protocolo v3" al iniciar.',
                            flush=True
                        )
                        break

                    if now - last_hello_request_at >= HANDSHAKE_RETRY_SECONDS:
                        last_hello_request_at = now
                        try:
                            self._send_line(source_socket, {
                                'type': 'HELLO_REQUEST',
                                'node_id': self.node_id,
                                'protocol_version': P2P_PROTOCOL_VERSION
                            })
                            print(f'\n -- HELLO_REQUEST enviado a {peer_id}', flush=True)
                        except OSError as e:
                            print(f'\n -- No se pudo pedir HELLO a {peer_id}: {e}', flush=True)
                            break

                    continue

                if peer_id:
                    print(
                        f'\n -- Timeout de lectura P2P con {peer_id}; cerrando conexion',
                        flush=True
                    )
                break
            except OSError as e:
                if peer_id and self._is_active_peer_socket(peer_id, source_socket):
                    print(f'\n -- Peer P2P desconectado ({peer_id}): {e}', flush=True)
                elif peer_id:
                    print(f'\n -- Conexion P2P cerrada antes de HELLO ({peer_id}): {e}', flush=True)
                break

            if not chunk:
                if peer_id and self._is_active_peer_socket(peer_id, source_socket):
                    print(f'\n -- Peer P2P cerro la conexion ({peer_id})', flush=True)
                elif peer_id:
                    print(f'\n -- Conexion P2P cerrada antes de HELLO ({peer_id})', flush=True)
                break

            buffer += chunk.decode('utf-8')

    def _handle_line(self, line, source_socket, peer_id=None, address=None):
        if not line.strip():
            return

        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(f'\n -- Mensaje P2P invalido ignorado: {e}')
            return

        if message.get('type') == 'HELLO':
            self._register_hello(peer_id, source_socket, address, message)
            return

        if message.get('type') == 'HELLO_REQUEST':
            if self.mode == 'peer':
                self._send_line(source_socket, self._hello_payload())
            return

        if message.get('type') == 'HELLO_ACK':
            return

        if self.mode == 'server' and peer_id and not self._is_active_peer_socket(peer_id, source_socket):
            print(
                f'\n -- Mensaje P2P ignorado antes de HELLO ({peer_id}): {message.get("type")}',
                flush=True
            )
            return

        if self.on_message:
            self.on_message(message, peer_id=peer_id)

        if self.mode == 'server' and message.get('type') not in ('SYNC_REQUEST', 'SYNC_STATE'):
            self._broadcast_to_clients(message, exclude_peer_id=peer_id)

    def _register_hello(self, peer_id, client_socket, address, message):
        if not peer_id:
            return

        node_id = message.get('node_id', peer_id)
        stale_clients = []
        already_registered = False

        with self.lock:
            already_registered = self.clients.get(peer_id) is client_socket

            for existing_peer_id, peer in list(self.peers.items()):
                if existing_peer_id != peer_id and peer.get('node_id') == node_id:
                    stale_socket = self.clients.pop(existing_peer_id, None)
                    self.peers.pop(existing_peer_id, None)

                    if stale_socket:
                        stale_clients.append(stale_socket)

            current = self.peers.get(peer_id, {})
            connected_at = current.get('connected_at', time.time())
            self.clients[peer_id] = client_socket
            self.peers[peer_id] = {
                **current,
                'peer_id': peer_id,
                'node_id': node_id,
                'address': address[0] if address else current.get('address'),
                'port': address[1] if address else current.get('port'),
                'connected_at': connected_at,
                'mode': message.get('mode', 'peer'),
                'protocol_version': message.get('protocol_version', 1)
            }

        self._set_socket_timeout(client_socket, None)
        self._send_line(client_socket, {
            'type': 'HELLO_ACK',
            'node_id': self.node_id,
            'peer_id': peer_id,
            'protocol_version': P2P_PROTOCOL_VERSION
        })

        for stale_socket in stale_clients:
            self._close_socket(stale_socket)

        if already_registered:
            print(
                f'\n -- HELLO P2P duplicado confirmado: {node_id} ({peer_id})',
                flush=True
            )
            return

        print(
            f'\n -- Peer P2P registrado: {node_id} ({peer_id}) '
            f'protocolo v{message.get("protocol_version", 1)}',
            flush=True
        )
        self._notify_sync_requested(peer_id)

    def send_to_peer(self, peer_id, message):
        with self.lock:
            client_socket = self.clients.get(peer_id)

        if not client_socket:
            return False

        try:
            self._send_line(client_socket, {
                **message,
                'origin_node_id': message.get('origin_node_id', self.node_id),
                'sent_at': time.time()
            })
            return True
        except OSError:
            self._drop_client(peer_id, client_socket)
            return False

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
        with self.root_lock:
            root_socket = self.root_socket

        if not root_socket:
            return

        try:
            self._send_line(root_socket, message)
        except OSError:
            with self.root_lock:
                if self.root_socket is root_socket:
                    self.root_socket = None

            self._close_socket(root_socket)

    def _send_line(self, destination_socket, message):
        payload = (json.dumps(message) + '\n').encode('utf-8')
        write_lock = self._write_lock(destination_socket)

        with write_lock:
            destination_socket.sendall(payload)

    def _hello_payload(self):
        return {
            'type': 'HELLO',
            'node_id': self.node_id,
            'mode': self.mode,
            'protocol_version': P2P_PROTOCOL_VERSION
        }

    def _wait_for_hello_ack(self, root_socket):
        buffer = ''
        deadline = time.time() + HANDSHAKE_TIMEOUT_SECONDS

        while True:
            try:
                chunk = root_socket.recv(65536)
            except socket.timeout:
                if time.time() >= deadline:
                    raise TimeoutError('El nodo raiz no confirmo HELLO dentro del tiempo esperado')

                self._send_line(root_socket, self._hello_payload())
                print('\n -- Reintentando HELLO con el nodo raiz P2P...', flush=True)
                continue

            if not chunk:
                raise ConnectionError('El nodo raiz cerro la conexion antes de confirmar HELLO')

            buffer += chunk.decode('utf-8')

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)

                if not line.strip():
                    continue

                message = json.loads(line)

                if message.get('type') == 'HELLO_ACK':
                    print(
                        f'\n -- HELLO_ACK recibido del nodo raiz '
                        f'(protocolo v{message.get("protocol_version", 1)})',
                        flush=True
                    )
                    return buffer

                if message.get('type') == 'HELLO_REQUEST':
                    self._send_line(root_socket, self._hello_payload())
                    continue

                raise ConnectionError(f'Respuesta P2P inesperada antes de HELLO_ACK: {message.get("type")}')

    def _drop_client(self, peer_id, client_socket):
        removed = False

        with self.lock:
            if self.clients.get(peer_id) is client_socket:
                self.clients.pop(peer_id, None)
                removed = True

            if self.peers.pop(peer_id, None) is not None:
                removed = True

        self._close_socket(client_socket)

        if removed:
            print(f'\n -- Peer P2P removido: {peer_id}', flush=True)

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

        with self.write_locks_lock:
            self.write_locks.pop(id(target_socket), None)

    def _write_lock(self, target_socket):
        socket_id = id(target_socket)

        with self.write_locks_lock:
            if socket_id not in self.write_locks:
                self.write_locks[socket_id] = threading.Lock()

            return self.write_locks[socket_id]

    def _is_active_peer_socket(self, peer_id, source_socket):
        with self.lock:
            return self.clients.get(peer_id) is source_socket

    def _notify_peers_changed(self):
        if self.mode != 'server' or not self.on_message:
            return

        try:
            self.on_message({'type': 'PEERS_CHANGED', 'node_id': self.node_id}, peer_id=None)
        except Exception as e:
            print(f'\n -- No se pudo publicar el cambio de peers P2P: {e}')

    def _notify_sync_requested(self, peer_id):
        if self.mode != 'server' or not self.on_message:
            return

        try:
            return self.on_message({
                'type': 'SYNC_REQUEST',
                'node_id': peer_id,
                'origin_node_id': peer_id
            }, peer_id=peer_id)
        except Exception as e:
            print(f'\n -- No se pudo sincronizar el peer P2P ({peer_id}): {e}')
            return False

    def _enable_tcp_low_latency(self, target_socket):
        try:
            target_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

    def _set_socket_timeout(self, target_socket, timeout):
        try:
            target_socket.settimeout(timeout)
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
