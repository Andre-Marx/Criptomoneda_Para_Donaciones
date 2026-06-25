import base64
import json
import os
import threading
import time
import uuid
import zlib

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from backend.socket_network import P2P_PROTOCOL_VERSION


PUBNUB_SUBSCRIBE_KEY = os.environ.get('PUBNUB_SUBSCRIBE_KEY', 'sub-c-79172fc9-a990-44d1-be43-95b76ed503a8')
PUBNUB_PUBLISH_KEY = os.environ.get('PUBNUB_PUBLISH_KEY', 'pub-c-9b1e180b-fb32-46ef-a9e3-461bf402cad3')
DEFAULT_CHANNEL = os.environ.get('P2P_CLOUD_CHANNEL', 'hopecoin-p2p-v3')
PUBNUB_CHUNK_TYPE = 'PUBNUB_CHUNK'
PUBNUB_MAX_DIRECT_CHARS = int(os.environ.get('P2P_PUBNUB_MAX_DIRECT_CHARS', '8000'))
PUBNUB_CHUNK_SIZE = int(os.environ.get('P2P_PUBNUB_CHUNK_SIZE', '6000'))
PUBNUB_CHUNK_TTL_SECONDS = int(os.environ.get('P2P_PUBNUB_CHUNK_TTL_SECONDS', '90'))
PUBNUB_HELLO_SYNC_COOLDOWN_SECONDS = int(
    os.environ.get('P2P_PUBNUB_HELLO_SYNC_COOLDOWN_SECONDS', '30')
)


class CloudListener(SubscribeCallback):
    def __init__(self, network):
        self.network = network

    def message(self, pubnub, message_object):
        self.network.handle_cloud_message(message_object.message)


class CloudNetwork:
    """
    Transporte P2P por PubNub.
    Sirve como alternativa cuando macOS/firewall bloquea conexiones LAN entrantes.
    """

    def __init__(self, node_id, on_message=None, mode='server', channel=DEFAULT_CHANNEL):
        self.node_id = node_id
        self.on_message = on_message
        self.mode = mode
        self.channel = channel
        self.pubnub = None
        self.started = False
        self.connected = False
        self.peers = {}
        self.incoming_chunks = {}
        self.hello_sync_sent_at = {}
        self.lock = threading.Lock()

    def start(self):
        if self.started:
            return

        self.started = True
        config = PNConfiguration()
        config.subscribe_key = PUBNUB_SUBSCRIBE_KEY
        config.publish_key = PUBNUB_PUBLISH_KEY
        config.uuid = self.node_id

        self.pubnub = PubNub(config)
        self.pubnub.add_listener(CloudListener(self))
        self.pubnub.subscribe().channels([self.channel]).execute()
        self.connected = True

        print(
            f'\n -- P2P PubNub iniciado en modo {self.mode} '
            f'(canal: {self.channel}, node_id: {self.node_id})',
            flush=True
        )

        threading.Thread(target=self._announce_loop, daemon=True).start()
        if self.mode == 'peer':
            threading.Thread(target=self._request_initial_sync, daemon=True).start()

    def status(self):
        with self.lock:
            peers = list(self.peers.values())
            pending_chunk_messages = len(self.incoming_chunks)

        return {
            'node_id': self.node_id,
            'mode': self.mode,
            'transport': 'pubnub',
            'channel': self.channel,
            'protocol_version': P2P_PROTOCOL_VERSION,
            'connected': self.connected,
            'peer_count': len(peers),
            'connection_count': len(peers),
            'peers': peers,
            'pending_chunk_messages': pending_chunk_messages
        }

    def broadcast(self, message):
        return self._publish(message)

    def send_to_peer(self, peer_id, message):
        return self._publish({
            **message,
            'target_node_id': peer_id
        })

    def handle_cloud_message(self, message):
        if not isinstance(message, dict):
            return

        origin_node_id = message.get('origin_node_id') or message.get('node_id')
        target_node_id = message.get('target_node_id')

        if origin_node_id == self.node_id:
            return

        if target_node_id and target_node_id != self.node_id:
            return

        if origin_node_id:
            self._remember_peer(origin_node_id, message)

        message_type = message.get('type')

        if message_type == PUBNUB_CHUNK_TYPE:
            self._handle_chunk(message, origin_node_id)
            return

        if message_type == 'HELLO':
            print(
                f'\n -- Peer PubNub visto: {origin_node_id} '
                f'(modo {message.get("mode", "desconocido")})',
                flush=True
            )
            if self._should_send_hello_sync(origin_node_id, message) and self.on_message:
                print(
                    f'\n -- Preparando sincronizacion inicial para peer PubNub {origin_node_id}...',
                    flush=True
                )
                self.on_message({
                    'type': 'SYNC_REQUEST',
                    'node_id': origin_node_id,
                    'origin_node_id': origin_node_id
                }, peer_id=origin_node_id)
            return

        if message_type == 'SYNC_STATE':
            print(
                f'\n -- PubNub recibio SYNC_STATE desde {origin_node_id}; '
                'aplicando estado recibido...',
                flush=True
            )

        if self.on_message:
            self.on_message(message, peer_id=origin_node_id)

    def _publish(self, message):
        if not self.pubnub:
            return False

        payload = {
            **message,
            'origin_node_id': message.get('origin_node_id', self.node_id),
            'node_id': message.get('node_id', self.node_id),
            'transport': 'pubnub',
            'sent_at': time.time()
        }

        return self._publish_payload(payload)

    def _publish_payload(self, payload):
        try:
            serialized_payload = self._serialize_payload(payload)
        except Exception as e:
            print(f'\n -- No se pudo serializar mensaje PubNub {payload.get("type")}: {e}', flush=True)
            return False

        if len(serialized_payload) <= PUBNUB_MAX_DIRECT_CHARS:
            return self._publish_raw(payload)

        return self._publish_chunked(payload, serialized_payload)

    def _publish_raw(self, payload):
        message_type = payload.get('type', 'desconocido')

        try:
            publish_request = self.pubnub.publish().channel(self.channel).message(payload)
            if hasattr(publish_request, 'use_post'):
                publish_request.use_post(True)
            publish_request.sync()
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            print(
                f'\n -- No se pudo publicar por PubNub ({message_type}): {e}',
                flush=True
            )
            return False

    def _publish_chunked(self, payload, serialized_payload):
        message_type = payload.get('type', 'desconocido')
        chunk_payloads = self._build_chunk_payloads(payload, serialized_payload)
        chunk_count = len(chunk_payloads)

        print(
            f'\n -- PubNub enviara {message_type} en {chunk_count} partes '
            f'({len(serialized_payload)} caracteres antes de comprimir).',
            flush=True
        )

        for index, chunk_payload in enumerate(chunk_payloads, start=1):
            if not self._publish_raw(chunk_payload):
                print(
                    f'\n -- PubNub fallo al enviar parte {index}/{chunk_count} de {message_type}.',
                    flush=True
                )
                return False

        print(
            f'\n -- PubNub publico {message_type} en {chunk_count} partes.',
            flush=True
        )
        return True

    def _build_chunk_payloads(self, payload, serialized_payload):
        compressed_payload = zlib.compress(serialized_payload.encode('utf-8'))
        encoded_payload = base64.b64encode(compressed_payload).decode('ascii')
        chunk_id = uuid.uuid4().hex
        chunks = [
            encoded_payload[index:index + PUBNUB_CHUNK_SIZE]
            for index in range(0, len(encoded_payload), PUBNUB_CHUNK_SIZE)
        ] or ['']

        return [
            {
                'type': PUBNUB_CHUNK_TYPE,
                'chunk_id': chunk_id,
                'chunk_index': index,
                'chunk_count': len(chunks),
                'chunk_data': chunk,
                'origin_node_id': payload.get('origin_node_id', self.node_id),
                'node_id': payload.get('node_id', self.node_id),
                'target_node_id': payload.get('target_node_id'),
                'original_type': payload.get('type'),
                'transport': 'pubnub',
                'sent_at': time.time()
            }
            for index, chunk in enumerate(chunks)
        ]

    def _handle_chunk(self, message, origin_node_id):
        chunk_id = message.get('chunk_id')
        chunk_data = message.get('chunk_data')
        original_type = message.get('original_type', 'desconocido')

        try:
            chunk_index = int(message.get('chunk_index'))
            chunk_count = int(message.get('chunk_count'))
        except (TypeError, ValueError):
            print('\n -- Chunk PubNub ignorado: indice invalido.', flush=True)
            return

        if not chunk_id or not isinstance(chunk_data, str) or chunk_count <= 0:
            print('\n -- Chunk PubNub ignorado: metadatos incompletos.', flush=True)
            return

        if chunk_index < 0 or chunk_index >= chunk_count:
            print('\n -- Chunk PubNub ignorado: indice fuera de rango.', flush=True)
            return

        now = time.time()
        with self.lock:
            self._discard_stale_chunks_locked(now)
            chunk_state = self.incoming_chunks.setdefault(chunk_id, {
                'origin_node_id': origin_node_id,
                'original_type': original_type,
                'chunk_count': chunk_count,
                'chunks': {},
                'received_at': now
            })

            if chunk_state['chunk_count'] != chunk_count:
                print('\n -- Chunk PubNub ignorado: total de partes inconsistente.', flush=True)
                return

            chunk_state['chunks'][chunk_index] = chunk_data
            received_count = len(chunk_state['chunks'])

        if received_count == 1 or received_count == chunk_count or received_count % 5 == 0:
            print(
                f'\n -- PubNub recibio parte {received_count}/{chunk_count} '
                f'de {original_type} desde {origin_node_id}.',
                flush=True
            )

        if received_count < chunk_count:
            return

        with self.lock:
            completed_state = self.incoming_chunks.pop(chunk_id, chunk_state)

        try:
            encoded_payload = ''.join(
                completed_state['chunks'][index]
                for index in range(completed_state['chunk_count'])
            )
            compressed_payload = base64.b64decode(encoded_payload.encode('ascii'))
            serialized_payload = zlib.decompress(compressed_payload).decode('utf-8')
            payload = json.loads(serialized_payload)
        except Exception as e:
            print(
                f'\n -- No se pudo rearmar mensaje PubNub {original_type}: {e}',
                flush=True
            )
            return

        print(
            f'\n -- PubNub rearma {original_type} desde '
            f'{completed_state["chunk_count"]} partes; entregando al protocolo P2P.',
            flush=True
        )
        self.handle_cloud_message(payload)

    def _announce_loop(self):
        while True:
            self._publish({
                'type': 'HELLO',
                'mode': self.mode,
                'protocol_version': P2P_PROTOCOL_VERSION
            })
            time.sleep(15)

    def _request_initial_sync(self):
        time.sleep(2)
        print('\n -- Solicitando sincronizacion inicial por PubNub...', flush=True)
        sent = self._publish({
            'type': 'SYNC_REQUEST',
            'node_id': self.node_id
        })
        print(
            f'\n -- Solicitud de sincronizacion PubNub enviada={sent}. '
            'Esperando SYNC_STATE del nodo raiz...',
            flush=True
        )

    def _should_send_hello_sync(self, origin_node_id, message):
        if self.mode != 'server' or message.get('mode') != 'peer' or not origin_node_id:
            return False

        now = time.time()
        with self.lock:
            last_sync_at = self.hello_sync_sent_at.get(origin_node_id, 0)
            if now - last_sync_at < PUBNUB_HELLO_SYNC_COOLDOWN_SECONDS:
                return False

            self.hello_sync_sent_at[origin_node_id] = now
            return True

    def _discard_stale_chunks_locked(self, now):
        stale_chunk_ids = [
            chunk_id
            for chunk_id, chunk_state in self.incoming_chunks.items()
            if now - chunk_state.get('received_at', now) > PUBNUB_CHUNK_TTL_SECONDS
        ]

        for chunk_id in stale_chunk_ids:
            self.incoming_chunks.pop(chunk_id, None)

    def _serialize_payload(self, payload):
        return json.dumps(payload, separators=(',', ':'), ensure_ascii=False)

    def _remember_peer(self, peer_id, message):
        with self.lock:
            self.peers[peer_id] = {
                'peer_id': peer_id,
                'node_id': peer_id,
                'mode': message.get('mode', 'peer'),
                'transport': 'pubnub',
                'last_seen_at': time.time(),
                'protocol_version': message.get('protocol_version', P2P_PROTOCOL_VERSION)
            }
