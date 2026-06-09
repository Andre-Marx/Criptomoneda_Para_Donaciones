import pytest
import time

from backend.blockchain.block import Block, GENESIS_DATA
from backend.config import MINE_RATE, SECONDS
from backend.util.hex_to_binary import hex_to_binary


def test_mine_block():
    '''
    Prueba que funcione el método de minado.
    '''

    last_block = Block.genesis()
    data = 'prueba-data'
    block = Block.mine_block(last_block, data)

    # Se valida que el bloque creado sea una instancia de la clase Block
    assert isinstance(block, Block)

    # Se valida que los datos sean los que recibió el bloque
    assert block.data == data

    # Se valida que coincida el hash anterior
    assert block.last_hash == last_block.hash

    assert hex_to_binary(block.hash)[0:block.difficulty] == '0'*block.difficulty


def test_genesis():
    '''
    Prueba que funcione correctamente el método del bloque génesis.
    '''

    genesis = Block.genesis()

    # Se valida que sea una instancia de la clase Block
    assert isinstance(genesis, Block)

    # Verifica que los argumentos del genesis sean los declaradis originalmente
    for key, value in GENESIS_DATA.items():
        assert getattr(genesis, key) == value


def test_quickly_mined_block():
    last_block = Block.mine_block(Block.genesis(), 'Prub')
    mined_block = Block.mine_block(last_block, 'minado')

    assert mined_block.difficulty == last_block.difficulty + 1


def test_slowly_mined_block():
    last_block = Block.mine_block(Block.genesis(), 'Prub')

    # Se aplica un atraso paraa que tarde en minar
    time.sleep(MINE_RATE / SECONDS)

    mined_block = Block.mine_block(last_block, 'minado')

    assert mined_block.difficulty == last_block.difficulty - 1


def test_mined_block_difficulty_limits_at_1():
    last_block = Block(
        time.time_ns(),
        'test_last_hash',
        'test_hash',
        'test_data',
        1,
        0,
        1
    )

    time.sleep(MINE_RATE / SECONDS)

    mined_block = Block.mine_block(last_block, 'minado')

    assert mined_block.difficulty == 1

# Se definen variables dentro de pytest para estarlas usando
@pytest.fixture
def last_block():
    return Block.genesis()

@pytest.fixture
def block(last_block):
    return Block.mine_block(last_block, 'prueba data')

def test_is_valid_block(last_block, block):
    Block.is_valid_block(last_block, block)

def test_is_valid_block_bad_last_hash(last_block, block):
    block.last_hash = 'evail_last_hash'

    # Para que python espere una excepción
    with pytest.raises(Exception, match = 'El "last_hash" del bloque debe ser correcto'):
        Block.is_valid_block(last_block, block)

def test_is_valid_block_bad_proof_of_work(last_block, block):
    block.hash = 'fff'

    # Para que python espere una excepción
    with pytest.raises(Exception, match = 'No se cumple la prueba de trabajo'):
        Block.is_valid_block(last_block, block)

def test_is_valid_block_jumped_difficulty(last_block, block):
    jumped_difficulty = 10
    block.difficulty = jumped_difficulty
    block.hash = f'{"0" * jumped_difficulty}111abc'

    # Para que python espere una excepción
    with pytest.raises(Exception, match = 'La dificultad ajustada del bloque sólo puede variar por 1'):
        Block.is_valid_block(last_block, block)

def test_id_valid_block_bad_block_hash(last_block, block):
    block.hash = '0000000000000000000000000adbbcc'
    # Para que python espere una excepción
    with pytest.raises(Exception, match = 'El hash del bloque debe ser correcto'):
        Block.is_valid_block(last_block, block)
