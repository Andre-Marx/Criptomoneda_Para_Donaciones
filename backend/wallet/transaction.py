import time
import uuid

from backend.wallet.wallet import Wallet
from backend.config import MINING_REWARD, MINING_REWARD_INPUT

class Transaction:
    """
    Documento de un cambio de moneda de un remitente a uno o más destinatarios.
    """
    def __init__(
        self,
        sender_wallet = None,
        recipient = None,
        amount = None,
        id = None,
        output = None,
        input = None,
        signatures = None,
        sender_balance = None
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.output = output or self.create_output(sender_wallet, recipient, amount, sender_balance)
        self.input = input or self.create_input(sender_wallet, self.output, sender_balance)
        self.signatures = signatures or self.create_signatures(
            sender_wallet,
            recipient,
            amount,
            self.input.get('signature') if self.input else None
        )

    def create_output(self, sender_wallet, recipient, amount, sender_balance = None):
        """
        Estructura de los datos de salida de una transacción.
        """
        balance = sender_balance if sender_balance is not None else sender_wallet.balance
        recipient_address = recipient.address if isinstance(recipient, Wallet) else recipient

        if amount > balance:
            raise Exception('El monto es mayor al balance')

        return {
            recipient_address: amount,
            sender_wallet.address: balance - amount
        }

    def create_input(self, sender_wallet, output, sender_balance = None):
        """
        Estructura de los datos de entrada de la transacción.
        Firma de la transacción y la dirección y llave pública del enviador.
        """
        balance = sender_balance if sender_balance is not None else sender_wallet.balance

        return {
            'timestamp': time.time_ns(),
            'amount': balance,
            'address': sender_wallet.address,
            'public_key':sender_wallet.public_key,
            'signature': sender_wallet.sign(output)
        }

    def create_signatures(self, sender_wallet, recipient, amount, sender_signature):
        """
        Guarda las firmas digitales que acompañan la transacción.
        """
        if not sender_wallet:
            return {}

        recipient_address = recipient.address if isinstance(recipient, Wallet) else recipient
        recipient_public_key = recipient.public_key if isinstance(recipient, Wallet) else None
        recipient_signature = None

        if isinstance(recipient, Wallet):
            recipient_signature = recipient.sign({
                'transaction_id': self.id,
                'sender_address': sender_wallet.address,
                'recipient_address': recipient_address,
                'amount': amount
            })

        return {
            'sender': {
                'address': sender_wallet.address,
                'public_key': sender_wallet.public_key,
                'signature': sender_signature
            },
            'recipient': {
                'address': recipient_address,
                'public_key': recipient_public_key,
                'signature': recipient_signature
            }
        }
    
    def update(self, sender_wallet, recipient, amount):
        """
        Actualiza la transacción con un existente o nuevo destinatario.
        """

        recipient_address = recipient.address if isinstance(recipient, Wallet) else recipient

        if amount > self.output[sender_wallet.address]:
            raise Exception('El monto es mayor al balance')

        if recipient_address in self.output:
            self.output[recipient_address] = self.output[recipient_address] + amount
        else:
            self.output[recipient_address] = amount

        self.output[sender_wallet.address] = self.output[sender_wallet.address] - amount

        self.input = self.create_input(sender_wallet, self.output, self.input['amount'])
        self.signatures = self.create_signatures(
            sender_wallet,
            recipient,
            amount,
            self.input['signature']
        )

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
        return Transaction(
            input=MINING_REWARD_INPUT,
            output={miner_wallet.address: MINING_REWARD}
        )



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
