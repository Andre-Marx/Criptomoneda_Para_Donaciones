import time

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback

from backend.blockchain.block import Block
from backend.wallet.transaction import Transaction


pnconfig = PNConfiguration()
pnconfig.subscribe_key = 'sub-c-79172fc9-a990-44d1-be43-95b76ed503a8'
pnconfig.publish_key = 'pub-c-9b1e180b-fb32-46ef-a9e3-461bf402cad3'

CHANNELS = {
    'TEST':'TEST',
    'BLOCK':'BLOCK',
    'TRANSACTION': 'TRANSACTION'
}


class Listener(SubscribeCallback):
    def __init__(self, blockchain, transaction_pool):
        self.blockchain = blockchain
        self.transaction_pool = transaction_pool

    def message(self, pubnub, message_object):
        print(f'\n-- Canal: {message_object.channel} | Mensaje: {message_object.message}')

        if message_object.channel == CHANNELS['BLOCK']:
            block = Block.from_json(message_object.message)
            potential_chain = self.blockchain.chain[:]
            potential_chain.append(block)

            try:
                self.blockchain.replace_chain(potential_chain)
                self.transaction_pool.clear_blockchain_transactions(self.blockchain)
                print('\n -- Se reemplazó con éxito la cadena local')
            except Exception as e:
                print(f'\n -- No se logró reemplazar la cadena: {e}')

        elif message_object.channel == CHANNELS['TRANSACTION']:
            transaction = Transaction.from_json(message_object.message)
            self.transaction_pool.set_transaction(transaction)
            print('\n -- Establecer la nueva transacción en el grupo de transacciones (transaction pool)')



class PubSub():
    """
    Maneja la capa publish/subscribe de la aplicación.
    Provee de comunicación entre los nodos de la red de blockchain.
    """
    def __init__(self, blockchain, transaction_pool):
        self.pubnub = PubNub(pnconfig)
        self.pubnub.subscribe().channels(CHANNELS.values()).execute()
        self.pubnub.add_listener(Listener(blockchain, transaction_pool))

    def publish(self, channel, message):
        """
        Publica el objeto mensaje en el canal.
        """
        
        # Nos desubscribimos para evitar duplicados al publicar un bloque nuevo.
        # self.pubnub.publish().channel(channel).message(message).sync() # Esta es la original

        self.pubnub.unsubscribe().channels([channel]).execute()
        self.pubnub.publish().channel(channel).message(message).sync()
        self.pubnub.subscribe().channels([channel]).execute()

    def broadcast_block(self, block):
        """
        Transmitir un objeto de bloque a todos los nodos.
        """
        self.publish(CHANNELS['BLOCK'], block.to_json())

    def broadcast_transaction(self, transaction):
        """
        Transmitir una transacción a todos los nodos.
        """
        self.publish(CHANNELS['TRANSACTION'], transaction.to_json())

def main():
    pubsub = PubSub()

    time.sleep(1)
    pubsub.publish(CHANNELS['TEST'], {'foo':'bar'})

if __name__ == '__main__':
    main()


