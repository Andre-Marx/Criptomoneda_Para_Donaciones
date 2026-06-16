import os

NANOSECONDS = 1
MICROSECONDS = 1000 * NANOSECONDS
MILLISECONDS = 1000 * MICROSECONDS
SECONDS = 1000 * MILLISECONDS

MINE_RATE = 4 * SECONDS

STARTING_BALANCE = 1000

MINING_REWARD = 50
MINING_REWARD_INPUT = {'address':'*--recompensa-oficial-de-mineria--*'}
ADDRESS_REWARD = '*--recompensa-oficial-de-mineria--*'

P2P_SOCKET_PORT = int(os.environ.get('P2P_SOCKET_PORT', 7000))
P2P_ROOT_PORT = int(os.environ.get('P2P_ROOT_PORT', P2P_SOCKET_PORT))
P2P_ROOT_HOST = os.environ.get('P2P_ROOT_HOST', '127.0.0.1')
P2P_MODE = os.environ.get('P2P_MODE', 'server').lower()
P2P_MINING_DIFFICULTY = int(os.environ.get('P2P_MINING_DIFFICULTY', 20))
