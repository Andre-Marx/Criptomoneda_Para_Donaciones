# -*- coding: utf-8 -*-
"""
@author: Andre-Puente
"""

import os
import time
from backend.util.crypto_hash import crypto_hash
from backend.config import MINE_RATE
from backend.util.hex_to_binary import hex_to_binary

GENESIS_DATA = {
    'timestamp':1,
    'last_merkle_root':'genesis_last_merkle_root',
    'merkle_root': crypto_hash([]),
    'proof_hash': 'genesis_proof_hash',
    'data': [],
    'difficulty':3,
    'nonce':'genesis_nonce',
    'number':1
}

class Block:
    """
    Bloque: Una unidad de almacenamiento.
    Almacenar transacciones en la Blockchain que admita una criptomoneda.
    """
    
    # Se inicializa un bloque
    def __init__(self, timestamp, last_merkle_root, merkle_root, proof_hash, data, difficulty, nonce, number):
        self.timestamp = timestamp
        self.last_merkle_root = last_merkle_root
        self.merkle_root = merkle_root
        self.proof_hash = proof_hash
        self.data = data
        self.difficulty = difficulty
        self.nonce = nonce
        self.number = number

        
    # Para representar el bloque
    def __repr__(self):
        return (
            'Block('
            f'timestamp: {self.timestamp}, '
            f'last_merkle_root: {self.last_merkle_root}, '
            f'merkle_root: {self.merkle_root}, '
            f'proof_hash: {self.proof_hash}, '
            f'data: {self.data}, '
            f'difficulty: {self.difficulty}, '
            f'nonce: {self.nonce}, '
            f'number: {self.number})'
            )

    def __eq__(self, other):
        """
        Compara los atributos de dos instancias de la clase.
        """
        return self.__dict__ == other.__dict__

    def to_json(self):
        """
        Serializa el bloque en un diccionario para almacenar sus atributos.
        """
        return self.__dict__

    @staticmethod
    def calculate_merkle_root(data):
        """Calcula la raíz de Merkle de las transacciones de un bloque.

        Cada elemento de ``data`` se convierte en una hoja hasheada. Si un
        nivel tiene un número impar de nodos, se duplica el último, que es la
        convención habitual para completar un árbol binario de Merkle.
        """
        hashes = [crypto_hash(item) for item in data] if isinstance(data, list) else [crypto_hash(data)]

        if not hashes:
            return crypto_hash([])

        while len(hashes) > 1:
            if len(hashes) % 2:
                hashes.append(hashes[-1])

            hashes = [
                crypto_hash(hashes[index], hashes[index + 1])
                for index in range(0, len(hashes), 2)
            ]

        return hashes[0]

    @staticmethod
    def mine_block(last_block, data, difficulty=None, progress_callback=None, stop_event=None):
        """
        Mina un bloque basado en el bloque anterior y datos dados, hasta que se encuentre un hash de bloque que cumpla con el requisito de prueba de trabajo del lìder 0.
        """
        timestamp = time.time_ns()
        last_merkle_root = last_block.merkle_root
        merkle_root = Block.calculate_merkle_root(data)
        difficulty = difficulty or Block.adjust_difficulty(last_block, timestamp)
        nonce = 0
        number = int(last_block.number) + 1
        proof_hash = crypto_hash(timestamp, last_merkle_root, merkle_root, difficulty, nonce, number)

        while hex_to_binary(proof_hash)[0:difficulty] != '0'*difficulty:
            if stop_event and stop_event.is_set():
                return None

            nonce += 1
            timestamp = time.time_ns()
            proof_hash = crypto_hash(timestamp, last_merkle_root, merkle_root, difficulty, nonce, number)

            if progress_callback and nonce % 1000 == 0:
                progress_callback({
                    'nonce': nonce,
                    'hash': proof_hash,
                    'difficulty': difficulty,
                    'timestamp': timestamp
                })
            #print(f'Nonce: {nonce} \nHash(transaccion + nonce): {hex_to_binary(hash)[0:10]}')

        if progress_callback:
            progress_callback({
                'nonce': nonce,
                'hash': proof_hash,
                'difficulty': difficulty,
                'timestamp': timestamp
            })
        
        return Block(timestamp, last_merkle_root, merkle_root, proof_hash, data, difficulty, nonce, number)
        
    @staticmethod
    def genesis():
        """
        Generador del bloque genesis.
        """
        return Block(**GENESIS_DATA)

    @staticmethod
    def from_json(block_json):
        """
        Convierte un bloque en formato json a una instancia de la clase bloque.
        """
        return Block(**block_json)

    @staticmethod
    def adjust_difficulty(last_block, new_timestamp):
        """
        Calcula la dificultad ajustada acorde al MINE_RATE.
        Incrementa la dificultad para los bloques extraídos rápidamente.
        Reduce la dificultad para bloques extraidos lentamente.
        """

        if(new_timestamp - last_block.timestamp) < MINE_RATE:
            return last_block.difficulty + 1

        if (last_block.difficulty - 1) > 0:
            return last_block.difficulty - 1

        return 1

    @staticmethod
    def is_valid_block(last_block, block):
        """
        Se valida un bloque de acuerdo con lo siguiente:
            - Debe tener la raíz de Merkle de su bloque inmediato anterior
            - Debe cumplir con la prueba de trabajo requerida
            - La dificultad debe ajustarse sólo por 1 valor (más o menos)
            - La raíz de Merkle debe representar correctamente los datos del bloque
        """
        if block.last_merkle_root != last_block.merkle_root:
            raise Exception('La raíz de Merkle anterior del bloque debe ser correcta')

        if hex_to_binary(block.proof_hash)[0:block.difficulty] != '0' * block.difficulty:
            raise Exception('No se cumple la prueba de trabajo')

        allow_competition_difficulty = os.environ.get('P2P_ALLOW_DIFFICULTY_JUMP') == 'True'

        if not allow_competition_difficulty and abs(last_block.difficulty - block.difficulty) > 1:
            raise Exception('La dificultad ajustada del bloque sólo puede variar por 1')

        if block.merkle_root != Block.calculate_merkle_root(block.data):
            raise Exception('La raíz de Merkle del bloque debe ser correcta')

        reconstructed_proof_hash = crypto_hash(
            block.timestamp,
            block.last_merkle_root,
            block.merkle_root,
            block.difficulty,
            block.nonce,
            block.number
        )

        if block.proof_hash != reconstructed_proof_hash:
            raise Exception('El hash de prueba de trabajo del bloque debe ser correcto')

def main():
    genesis_block = Block.genesis()
    bad_block = Block.mine_block(genesis_block, 'foo')
    print(bad_block)
    bad_block.last_merkle_root = 'evil_data'

    try:
        Block.is_valid_block(genesis_block, bad_block)
    except Exception as e:
        print(f'is_valid_block: {e}')

if __name__ == '__main__':
    main()
