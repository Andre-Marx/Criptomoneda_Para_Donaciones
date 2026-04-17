import time

from backend.blockchain.blockchain import Blockchain
from backend.config import SECONDS

blockchain = Blockchain()

# Para gaurdar cuanto tardan en minar los bloques
times = []

for i in range(100):
    start_time = time.time_ns()
    blockchain.add_block(i)
    end_time = time.time_ns()

    time_to_mine = (end_time - start_time) / SECONDS
    times.append(time_to_mine)

    # Se obtienen los segundos promedios
    average_time = sum(times) / len(times)

    print(f'------ Iteracion {i} ------')
    print(f'Difiutad de un nuevo bloque: {blockchain.chain[-1].difficulty}')
    print(f'Tiempo para minar un nuevo bloque: {time_to_mine}s')
    print(f'Tiempo promedio para añadir bloques: {average_time}s')
    print(f'Hash: {blockchain.chain[-1].hash}')
    print(f'Nonce: {blockchain.chain[-1].nonce}\n')
