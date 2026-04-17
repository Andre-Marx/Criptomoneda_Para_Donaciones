import json
#import uuid
import hashlib
import base58

from backend.config import STARTING_BALANCE
# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.utils import (encode_dss_signature, decode_dss_signature)
# from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

class Wallet:
    """
    Una billetera de un minero.
    Mantiene el registro del balance de los mineros.
    Permite a los mineros autorizar transacciones.
    """

    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        #self.address = str(uuid.uuid4())[:8]
        # self.private_key = ec.generate_private_key(ec.ed25519(), default_backend)
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.address = self.generate_address()
        self.serialize_public_key()

    @property
    def balance(self):
        return Wallet.calculate_balance(self.blockchain, self.address)

    def sign(self, data):
        """
        Genera la firma basada en los datos y la llave privada local.
        """
        data_hashing = hashlib.sha512(str(data).encode('utf-8')).digest()
        # return self.private_key.sign(data_hashing)

        # print(f'\nFirma: {self.private_key.sign(data_hashing)}')
        return int.from_bytes(self.private_key.sign(data_hashing)[:32], 'little'), int.from_bytes(self.private_key.sign(data_hashing)[32:], 'little')

    def serialize_public_key(self):
        """
        Serializa la llave pública para que sea un objeto nativo de python.
        """

        self.public_key = self.public_key.public_bytes(
            encoding = serialization.Encoding.PEM, 
            format = serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')

    def generate_address(self):
        """
        Genera la dirección de una billetera partiendo de la clave pública usando el algoritmo de Pay-to-Public-Key-Hash (P2PKH).
        """
        # Paso 1: SHA-256 de la clave pública
        sha256_hash = hashlib.sha256(self.public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).digest()

        # Paso 2: RIPEMD-160 del resultado del paso 1
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

        # Paso 3: Agregar un byte de versión (0x00 para direcciones P2PKH en la red principal de Bitcoin)
        version_byte = b'\x00'
        extended_ripemd160_hash = version_byte + ripemd160_hash

        # Paso 4: Calcular el checksum de la versión + hash160
        checksum = hashlib.sha256(hashlib.sha256(extended_ripemd160_hash).digest()).digest()[:4]

        # Paso 5: Concatenar la versión + hash160 + checksum
        binary_address = extended_ripemd160_hash + checksum

        # Paso 6: Codificar en Base58Check
        address = base58.b58encode(binary_address)

        return address.decode()

    @staticmethod
    def verify(public_key, data, signature):
        """
        Verifica una firma basada en la llave pública y datos originales.
        """
        data_hashing = hashlib.sha512(str(data).encode('utf-8')).digest()

        # Se convierte en una instancia de cryptography
        deserialized_public_key = serialization.load_pem_public_key(public_key.encode('utf-8'))

        # print(f'\nsignature: {signature}\n')

        (r,s) = signature 

        # print(f"\nFirma Regreso: {(r.to_bytes(32, 'little') + s.to_bytes(32, 'little'))}")

        try:
            deserialized_public_key.verify((r.to_bytes(32, 'little') + s.to_bytes(32, 'little')), data_hashing)
            return True

        except InvalidSignature:
            return False

    @staticmethod
    def calculate_balance(blockchain, address):
        """
        Calcule el saldo de la dirección dada teniendo en cuenta los datos de la transacción dentro de la cadena de bloques.
        
        El saldo se encuentra sumando los valores de salida que pertenecen a la dirección desde la transacción más reciente realizada por esa dirección.
        """
        balance = STARTING_BALANCE

        if not blockchain:
            return balance

        for block in blockchain.chain:
            for transaction in block.data:
                if transaction['input']['address'] == address:
                    # Cada vez que la dirección realiza una nueva transacción, restablece su saldo.
                    balance = transaction['output'][address]
                elif address in transaction['output']:
                    balance += transaction['output'][address]

        return balance


def main():
    wallet = Wallet()
    print(f'\nTipo de Objeto: {type(wallet)}')
    print(f'\nCompara Tipo de Objeto: {isinstance(wallet,  Wallet)}')
    print(f'\nwallet.__dict__: {wallet.__dict__}')
    
    data = {'foo': 'bar'}
    # data = 'foo'
    signature = wallet.sign(data)
    print(f'\nsignature: {signature}')

    should_be_valid = Wallet.verify(wallet.public_key, data, signature)
    print(f'\nshould_be_valid: {should_be_valid}')

    should_be_invalid = Wallet.verify(Wallet().public_key, data, signature)
    print(f'\nshould_be_invalid: {should_be_invalid}')

if __name__ == '__main__':
    main()