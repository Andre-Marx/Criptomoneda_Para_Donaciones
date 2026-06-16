# -*- coding: utf-8 -*-
"""
@author: Andre-Puente
"""

import time
from backend.util.crypto_hash import crypto_hash
from backend.config import MINE_RATE
from backend.util.hex_to_binary import hex_to_binary

GENESIS_DATA = {
    'timestamp':1,
    'last_hash':'genesis_last_hash',
    'hash': 'genesis_hash',
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
    def __init__(self, timestamp, last_hash, hash, data, difficulty, nonce, number):
        self.timestamp = timestamp
        self.last_hash = last_hash
        self.hash = hash
        self.data = data
        self.difficulty = difficulty
        self.nonce = nonce
        self.number = number

        
    # Para representar el bloque
    def __repr__(self):
        return (
            'Block('
            f'timestamp: {self.timestamp}, '
            f'last_hash: {self.last_hash}, '
            f'hash: {self.hash}, '
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
    def mine_block(last_block, data):
        """
        Mina un bloque basado en el bloque anterior y datos dados, hasta que se encuentre un hash de bloque que cumpla con el requisito de prueba de trabajo del lìder 0.
        """
        timestamp = time.time_ns()
        last_hash = last_block.hash
        difficulty = Block.adjust_difficulty(last_block, timestamp)
        nonce = 0
        number = int(last_block.number) + 1
        hash = crypto_hash(timestamp, last_hash, data, difficulty, nonce, number)

        while hex_to_binary(hash)[0:difficulty] != '0'*difficulty:
            nonce += 1
            timestamp = time.time_ns()
            difficulty = Block.adjust_difficulty(last_block, timestamp)
            hash = crypto_hash(timestamp, last_hash, data, difficulty, nonce, number)
            #print(f'Nonce: {nonce} \nHash(transaccion + nonce): {hex_to_binary(hash)[0:10]}')
        
        return Block(timestamp, last_hash, hash, data, difficulty, nonce, number)
        
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
            - Debe tener la referencia al hash de su bloque inmediato anterior (last_hash)
            - Debe cumplir con la prueba de trabajo requerida
            - La dificultad debe ajustarse sólo por 1 valor (más o menos)
            - El hash de un bloque, debe ser una combinación válida de los campos del mismo
        """
        if block.last_hash != last_block.hash:
            raise Exception('El "last_hash" del bloque debe ser correcto')

        if hex_to_binary(block.hash)[0:block.difficulty] != '0' * block.difficulty:
            raise Exception('No se cumple la prueba de trabajo')

        if abs(last_block.difficulty - block.difficulty) > 1:
            raise Exception('La dificultad ajustada del bloque sólo puede variar por 1')

        reconstructed_hash = crypto_hash(
            block.timestamp,
            block.last_hash,
            block.data,
            block.difficulty,
            block.nonce,
            block.number
        )

        if block.hash != reconstructed_hash:
            raise Exception('El hash del bloque debe ser correcto')

def main():
    genesis_block = Block.genesis()
    bad_block = Block.mine_block(genesis_block, 'foo')
    print(bad_block)
    bad_block.last_hash = 'evil_data'

    try:
        Block.is_valid_block(genesis_block, bad_block)
    except Exception as e:
        print(f'is_valid_block: {e}')

if __name__ == '__main__':
    main()
