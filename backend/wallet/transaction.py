import time
import uuid

from backend.wallet.wallet import Wallet
from backend.config import MINING_REWARD, ADDRESS_REWARD

class Transaction:
    """
    Documento de un cambio de moneda de un remitente a uno o más destinatarios.
    """
    def __init__(self, sender_wallet = None, recipient = None, amount = None, id = None, output = None, input = None):
        self.id = id or str(uuid.uuid4())[:8]
        self.output = output or self.create_output(sender_wallet, recipient, amount)
        self.input = input or self.create_input(sender_wallet, self.output)

    def create_output(self, sender_wallet, recipient, amount):
        """
        Estructura de los datos de salida de una transacción.
        """
        if amount >  sender_wallet.balance:
            raise Exception('El monto es mayor al balance')

        output = {}

        if isinstance(recipient,  Wallet):
            output['recipients_address'] = recipient.address
            output['amount_received'] = amount
            output['recipients_signature'] = recipient.sign({'sender_address': sender_wallet.address, 'amount':amount})
            output['recipients_public_key'] = recipient.public_key
            output['sender_balance'] = sender_wallet.balance - amount
            output[sender_wallet.address] = sender_wallet.balance - amount
        else:
            output[recipient] = amount
            output[sender_wallet.address] = sender_wallet.balance - amount

        

        return output

    def create_input(self, sender_wallet, output):
        """
        Estructura de los datos de entrada de la transacción.
        Firma de la transacción y la dirección y llave pública del enviador.
        """

        return {
            'timestamp': time.time_ns(),
            'amount': sender_wallet.balance,
            'address': sender_wallet.address,
            'public_key':sender_wallet.public_key,
            'signature': sender_wallet.sign(output)
        }
    
    def update(self, sender_wallet, recipient, amount):
        """
        Actualiza la transacción con un existente o nuevo destinatario.
        """

        if amount > self.output[sender_wallet.address]:
            raise Exception('El monto es mayor al balance')

        if recipient in self.output:
            self.output[recipient] = self.output[recipient] + amount
        else:
            self.output[recipient] = amount

        self.output[sender_wallet.address] = self.output[sender_wallet.address] - amount

        self.input = self.create_input(sender_wallet, self.output)

    def to_json(self):
        """
        Serializa la transacción.
        """
        return self.__dict__

    @staticmethod
    def from_json(transaction_json):
        """
        Deserializar la representación json de una transacción de nuevo en una instancia de transacción.
        """
        return Transaction(**transaction_json)


    @staticmethod
    def is_valid_transaction(transaction):
        """
        Valdia una transacción.
        Regresa una excepción para transacciones inválidas.
        """
        if transaction.input == MINING_REWARD_INPUT:
            if list(transaction.output.values()) != [MINING_REWARD]:
                raise Exception('Recompensa de mineria invalida')
            return

        output_total = sum(transaction.output.values())

        if transaction.input['amount'] != output_total:
            raise Exception('Valores de salida de transacción inválidos')

        if not Wallet.verify(transaction.input['public_key'], transaction.output, transaction.input['signature']):
            raise Exception('Firma Inválida')

    @staticmethod
    def reward_transaction(miner_wallet):
        """
        Genera la recompensa por minar una transaccion
        """
        output = {}
        output[miner_wallet.address] = MINING_REWARD 

        return Transaction(input= {
            'timestamp': time.time_ns(),
            'amount': '',
            'address': ADDRESS_REWARD,
            'public_key': '',
            'signature': ''
        }, output = {
            'recipients_address': miner_wallet.address,
            'amount_received': MINING_REWARD,
            'recipients_signature': 'AUTO',
            'recipients_public_key': miner_wallet.public_key,
            'sender_balance': '',
            miner_wallet.address: MINING_REWARD
        })



def main():
    print('----- Transacción de Prueba -----')
    transaction = Transaction(Wallet(), 'recipient', 15)
    print(f'transaction.__dict__: {transaction.__dict__}')

    transaction_json = transaction.to_json()
    restored_transaction = Transaction.from_json(transaction_json)
    print(f'\nrestored_transaction.__dict__: {restored_transaction.__dict__}')

    print('\n----- Transacción entre billeteras -----')
    wallet1 = Wallet()
    wallet2 = Wallet()
    transaction = Transaction(wallet1, wallet2, 15)
    print(f'transaction.__dict__: {transaction.__dict__}')


if __name__ == '__main__':
    main()