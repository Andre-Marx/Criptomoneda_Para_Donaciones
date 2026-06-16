from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.transaction import Transaction
from backend.wallet.wallet import Wallet
from backend.blockchain.blockchain import Blockchain

def test_set_transaction():
    transaction_pool = TransactionPool()
    transaction = Transaction(Wallet(), 'recipient', 1)
    transaction_pool.set_transaction(transaction)

    assert transaction_pool.transaction_map[transaction.id] == transaction

def test_clear_blockchain_transactions():
    transaction_pool = TransactionPool()
    transaction_1 = Transaction(Wallet(), 'recipient', 1)
    transaction_2 = Transaction(Wallet(), 'recipient', 2)

    transaction_pool.set_transaction(transaction_1)
    transaction_pool.set_transaction(transaction_2)

    blockchain = Blockchain()
    blockchain.add_block([transaction_1.to_json(), transaction_2.to_json()])

    assert transaction_1.id in transaction_pool.transaction_map
    assert transaction_2.id in transaction_pool.transaction_map

    transaction_pool.clear_blockchain_transactions(blockchain)

    assert not transaction_1.id in transaction_pool.transaction_map
    assert not transaction_2.id in transaction_pool.transaction_map

def test_available_balance_accounts_for_pending_transactions():
    transaction_pool = TransactionPool()
    blockchain = Blockchain()
    wallet = Wallet(blockchain)

    transaction_1 = Transaction(wallet, 'recipient', 100)
    transaction_pool.set_transaction(transaction_1)

    assert transaction_pool.available_balance(blockchain, wallet.address) == wallet.balance - 100

    transaction_2 = Transaction(
        wallet,
        'recipient_2',
        200,
        sender_balance=transaction_pool.available_balance(blockchain, wallet.address)
    )
    transaction_pool.set_transaction(transaction_2)

    assert transaction_pool.available_balance(blockchain, wallet.address) == wallet.balance - 300
