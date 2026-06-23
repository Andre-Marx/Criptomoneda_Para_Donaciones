# -*- coding: utf-8 -*-
"""
@author: Andre-Puente
"""
import hashlib
import json



def crypto_hash(*args):
    """
    Regresa la función hash SHA-512 aplicada a argumentos dados.
    """
    
    # Obtiene la representación en string de cualquier dato dado
    stringified_args = sorted(map(lambda data: json.dumps(data, sort_keys=True), args))
    # print(f'stringified_args: {stringified_args}')
    joined_data = ''.join(stringified_args)
    # print(f'joined_data: {joined_data}')
    
    return hashlib.sha512(joined_data.encode('utf-8')).hexdigest()


def main():
    print(f'crypto_hash("uno", 2, [3]: {crypto_hash("uno", 2, [3])}')
    print(f'crypto_hash(2, "uno", [3]: {crypto_hash(2, "uno", [3])}')
    
if __name__ == '__main__':
    main()
