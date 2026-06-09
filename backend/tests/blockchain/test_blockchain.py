import pytest

from backend.blockchain.blockchain import Blockchain
from backend.wallet.wallet import Wallet
from backend.wallet.transaction import Transaction
from backend.blockchain.block import GENESIS_DATA

def test_blockchain_instance():
    '''
    Valida las instancias de la cadena
    '''
    
    blockchain = Blockchain()
    assert blockchain.chain[0].hash == GENESIS_DATA['hash']


def test_add_block():
    '''
    Valida cuando se añade un bloque nuevo
    '''

    blockchain = Blockchain()
    data = 'prueba-data'
    blockchain.add_block(data)

    assert blockchain.chain[-1].data == data


@pytest.fixture
def blockchain_three_blocks():
    blockchain = Blockchain()
    for i in range(3):
        blockchain.add_block([Transaction(Wallet(), 'recipient', i).to_json()])
    return blockchain

def test_is_valid_chain(blockchain_three_blocks):
    Blockchain.is_valid_chain(blockchain_three_blocks.chain)

def test_is_valid_chain_bad_genesis(blockchain_three_blocks):
    blockchain_three_blocks.chain[0].hash = 'evil_hash'

    with pytest.raises(Exception, match = 'El bloque genesis debe ser valido'):
        Blockchain.is_valid_chain(blockchain_three_blocks.chain)

def test_replace_chain(blockchain_three_blocks):
    blockchain = Blockchain()
    blockchain.replace_chain(blockchain_three_blocks.chain)

    # Se prueba que sirva el reemplazo
    assert blockchain.chain == blockchain_three_blocks.chain


def test_replace_chain_not_longer(blockchain_three_blocks):
    blockchain = Blockchain()

    with pytest.raises(Exception, match = 'La cadena entrante debe ser más larga'):
        blockchain_three_blocks.replace_chain(blockchain.chain)

def test_replace_chain_bad_chain(blockchain_three_blocks):
    blockchain = Blockchain()
    blockchain_three_blocks.chain[1].hash = 'evil_hash'

    with pytest.raises(Exception, match = 'La cadena entrante es invalida'):
        blockchain.replace_chain(blockchain_three_blocks.chain)

def test_valid_transaction_chain(blockchain_three_blocks):
    Blockchain.is_valid_transaction_chain(blockchain_three_blocks.chain)

def test_is_valid_transaction_chain_duplicates_transactions(blockchain_three_blocks):
    transaction = Transaction(Wallet(), 'recipient', 1).to_json()

    blockchain_three_blocks.add_block([transaction, transaction])

    with pytest.raises(Exception, match = 'no es único'):
        Blockchain.is_valid_transaction_chain(blockchain_three_blocks.chain)

def test_is_valid_transaction_chain_multiple_rewards(blockchain_three_blocks):
    reward_1 = Transaction.reward_transaction(Wallet()).to_json()
    reward_2 = Transaction.reward_transaction(Wallet()).to_json()

    blockchain_three_blocks.add_block([reward_1, reward_2])

    with pytest.raises(Exception, match = 'Sólo puede haber una recompensa de minería por bloque'):
        Blockchain.is_valid_transaction_chain(blockchain_three_blocks.chain)

def test_is_valid_transaction_chain_bad_transaction(blockchain_three_blocks):
    bad_transaction = Transaction(Wallet(), 'recipient', 1)
    bad_transaction.input['signature'] = Wallet().sign(bad_transaction.output)
    blockchain_three_blocks.add_block([bad_transaction.to_json()])

    with pytest.raises(Exception):
        Blockchain.is_valid_transaction_chain(blockchain_three_blocks.chain)

def test_is_valid_transaction_chain_bad_historic_balance(blockchain_three_blocks):
    wallet = Wallet()
    bad_transaction = Transaction(wallet, 'recipient', 1)
    bad_transaction.output[wallet.address] = 9000
    bad_transaction.input['amount'] = 9001
    bad_transaction.input['signature'] = wallet.sign(bad_transaction.output)

    blockchain_three_blocks.add_block([bad_transaction.to_json()])

    with pytest.raises(Exception, match = 'tiene un monto inválido como input'):
        Blockchain.is_valid_transaction_chain(blockchain_three_blocks.chain)
