# -*- coding: utf-8 -*-
"""
@author: Andre-Puente
"""

from backend.blockchain.block import Block
from backend.wallet.transaction import Transaction
from backend.wallet.wallet import Wallet
from backend.config import MINING_REWARD_INPUT


class Blockchain:
    """
    Blockchain: Es un libro público de transacciones.
    Implementado como lista de bloques - conjunto de datos de transacciones.
    """
    
    # Se inicializa una cadena
    def __init__(self):
        self.chain = [Block.genesis()]
        
    # Se agregan bloques a la cadena
    def add_block(self, data):
        self.chain.append(Block.mine_block(self.chain[-1], data))
        
        
    # Para ver la cadena
    def __repr__(self):
        return f'Blockchain: {self.chain}'

    def replace_chain(self, chain):
        """
        Reemplaza la cadna local con la entrante si comple con las siguientes reglas:
            - La cadena entrante es más larga que la local
            - La cadena entrante tiene el formato adecuado
        """
        if len(chain) <= len(self.chain):
            raise Exception('No se puede reemplazar. La cadena entrante debe ser más larga.')

        try:
            Blockchain.is_valid_chain(chain)
        except Exception as e:
            raise Exception(f'No se puede reemplazar. La cadena entrante es invalida: {e}')

        # Se hace el reemplazo
        self.chain = chain

    def to_json(self):
        """
        Serializar la cadena de bloques en una lista de bloques.
        """
        return list(map(lambda block: block.to_json(), self.chain))

    @staticmethod
    def from_json(chain_json):
        """
        Convierte una cadena en formato json a una instancia de la clase Blockchain.
        El resultado contendrá una cadena que contiene una lista de instancias de la clase Block.
        """
        blockchain = Blockchain()
        blockchain.chain = list(map(lambda block_json: Block.from_json(block_json), chain_json))

        return blockchain

    @staticmethod
    def is_valid_chain(chain):
        """
        Se realizan validaciones siguiendo las siguientes reglas:
            - La cadena debe empezar con el bloque genesis
            - Los bloques deben tener el formato correcto
        """

        if chain[0] != Block.genesis():
            raise Exception('El bloque genesis debe ser valido')

        for i in range(1, len(chain)):
            block = chain[i]
            last_block = chain[i-1]
            Block.is_valid_block(last_block, block)

        Blockchain.is_valid_transaction_chain(chain)

    @staticmethod
    def is_valid_transaction_chain(chain):
        """
        Hacer cumplir las reglas de una cadena compuesta por bloques de transacciones.
            - Cada transacción solo debe aparecer una vez en la cadena
            - Solo puede haber una recompensa de minería por bloque
            - Cada transacción debe ser válida
        """
        transaction_ids = set()
        address_balances = {}

        for i in range(len(chain)):
            block = chain[i]
            has_mining_reward = False

            for transaction_json in block.data:
                transaction = Transaction.from_json(transaction_json)

                if transaction.id in transaction_ids:
                    raise Exception(f'Transacción: {transaction.id} no es único')

                transaction_ids.add(transaction.id)

                if transaction.input == MINING_REWARD_INPUT:
                    if has_mining_reward:
                        raise Exception(f'Sólo puede haber una recompensa de minería por bloque. \n Revisar el bloque con hash: {block.hash}')
                    has_mining_reward = True
                    Transaction.is_valid_transaction(transaction)

                    for recipient, amount in transaction.output.items():
                        if recipient not in address_balances:
                            historic_blockchain = Blockchain()
                            historic_blockchain.chain = chain[0:i]
                            address_balances[recipient] = Wallet.calculate_balance(historic_blockchain, recipient)

                        address_balances[recipient] += amount

                else:
                    sender_address = transaction.input['address']

                    if sender_address not in address_balances:
                        historic_blockchain = Blockchain()
                        historic_blockchain.chain = chain[0:i]
                        address_balances[sender_address] = Wallet.calculate_balance(historic_blockchain, sender_address)

                    if address_balances[sender_address] != transaction.input['amount']:
                        raise Exception(f'Transacción {transaction.id} tiene un monto inválido como input')

                    Transaction.is_valid_transaction(transaction)

                    for recipient, amount in transaction.output.items():
                        if recipient == sender_address:
                            address_balances[recipient] = amount
                            continue

                        if recipient not in address_balances:
                            historic_blockchain = Blockchain()
                            historic_blockchain.chain = chain[0:i]
                            address_balances[recipient] = Wallet.calculate_balance(historic_blockchain, recipient)

                        address_balances[recipient] += amount

# Se crea la clase main para ayudarnos al momento de debuggear
def main():
    # Pruebo esta primer cadena
    blockchain = Blockchain()
    blockchain.add_block('1')
    blockchain.add_block('2')
    
    print(blockchain)
    print(f'blockchain.py __name__: {__name__}')
    
if __name__ == '__main__':
    main()
