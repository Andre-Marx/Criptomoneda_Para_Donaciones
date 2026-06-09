import pytest

import backend.wallet.transaction as transaction_module
from backend.config import MINING_REWARD_INPUT


@pytest.fixture(autouse=True)
def patch_mining_reward_input(monkeypatch):
    monkeypatch.setattr(
        transaction_module,
        'MINING_REWARD_INPUT',
        MINING_REWARD_INPUT,
        raising=False
    )
