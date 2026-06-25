import os
import threading
import time

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from backend.socket_network import P2P_PROTOCOL_VERSION


PUBNUB_SUBSCRIBE_KEY = os.environ.get('PUBNUB_SUBSCRIBE_KEY', 'sub-c-79172fc9-a990-44d1-be43-95b76ed503a8')
PUBNUB_PUBLISH_KEY = os.environ.get('PUBNUB_PUBLISH_KEY', 'pub-c-9b1e180b-fb32-46ef-a9e3-461bf402cad3')
DEFAULT_CHANNEL = os.environ.get('P2P_CLOUD_CHANNEL', 'hopecoin-p2p-v3')


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

        return {
            'node_id': self.node_id,
            'mode': self.mode,
            'transport': 'pubnub',
            'channel': self.channel,
            'protocol_version': P2P_PROTOCOL_VERSION,
            'connected': self.connected,
            'peer_count': len(peers),
            'connection_count': len(peers),
            'peers': peers
        }

    def broadcast(self, message):
        self._publish(message)

    def send_to_peer(self, peer_id, message):
        self._publish({
            **message,
            'target_node_id': peer_id
        })
        return True

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

        if message_type == 'HELLO':
            print(
                f'\n -- Peer PubNub visto: {origin_node_id} '
                f'(modo {message.get("mode", "desconocido")})',
                flush=True
            )
            if self.mode == 'server' and message.get('mode') == 'peer' and self.on_message:
                self.on_message({
                    'type': 'SYNC_REQUEST',
                    'node_id': origin_node_id,
                    'origin_node_id': origin_node_id
                }, peer_id=origin_node_id)
            return

        if self.on_message:
            self.on_message(message, peer_id=origin_node_id)

    def _publish(self, message):
        if not self.pubnub:
            return

        payload = {
            **message,
            'origin_node_id': message.get('origin_node_id', self.node_id),
            'node_id': message.get('node_id', self.node_id),
            'transport': 'pubnub',
            'sent_at': time.time()
        }

        try:
            self.pubnub.publish().channel(self.channel).message(payload).sync()
        except Exception as e:
            self.connected = False
            print(f'\n -- No se pudo publicar por PubNub: {e}', flush=True)

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
        self._publish({
            'type': 'SYNC_REQUEST',
            'node_id': self.node_id
        })

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
