class TransactionPool:
    def __init__(self):
        self.transaction_map = {}

    def set_transaction(self, transaction):
        """
        Establece una transacción en el grupo de transacciones (transaction pool).
        """
        self.transaction_map[transaction.id] = transaction

    def existing_transaction(self, address):
        """
        Encuentre una transacción generada por la dirección en el grupo de transacciones. 
        """
        for transaction in self.transaction_map.values():
            if transaction.input['address'] == address:
                return transaction

    def transaction_data(self):
        """
        Regresa las transacciones en formato json.
        """

        return list(map(lambda transaction: transaction.to_json(), self.transaction_map.values()))

    def clear_blockchain_transactions(self, blockchain):
        """
        Borra el registro que se tiene de transacciones en la cadena del transaction pool.
        """

        for block in blockchain.chain:
            for transaction in block.data:
                try:
                    del self.transaction_map[transaction['id']]
                except KeyError:
                    pass