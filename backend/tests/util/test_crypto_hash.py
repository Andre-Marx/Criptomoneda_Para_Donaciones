from backend.util.crypto_hash import crypto_hash

def test_crypto_hash():
    # Debería crear el mismo hash para diferentes tipos de datos como argumentos sin importar su orden 
    assert crypto_hash(1, [2], 'tres') == crypto_hash('tres', 1, [2])
    assert crypto_hash('Prub') == '74a29d6fbf21cbe7a3ed18f549d4c7a8c92cf403d7359fbcc242043ea987f054995823cfc29e70e85221fff3f5df79d8828a1f6b4f5a529bed49d5ff3db8719f'

    