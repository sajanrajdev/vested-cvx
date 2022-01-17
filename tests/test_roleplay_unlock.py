import pytest
import brownie
from brownie import *
from helpers.constants import MaxUint256
from eth_utils import encode_hex

"""
  Checks that ratio changes allow different investment profiles
"""

SETT_ADDRESS = "0xfd05D3C7fe2924020620A8bE4961bBaA747e6305"

STRAT_ADDRESS = "0x3ff634ce65cDb8CC0D569D6d1697c41aa666cEA9"

@pytest.fixture
def strat_proxy():
    return MyStrategy.at(STRAT_ADDRESS)
@pytest.fixture
def sett_proxy():
    return SettV4.at(SETT_ADDRESS)

@pytest.fixture
def real_strategist(strat_proxy):
    return accounts.at(strat_proxy.strategist(), force=True)

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

KNOWN_UNLOCK_TIME = 1642636800 ## Change every time you need to make the experiment

LOCK_INDEX = 1 ## UNUSED, convenience

EXPECTED_AMOUNT = 70758564549617397695572 ## Used to check we get the amount from lock
## just go to https://etherscan.io/address/0xd18140b4b819b895a3dba5442f959fa44994af50#readContract
## userLocks and get the amount and time to lock so you can run an accurate test each week / unlock period

def test_real_world_unlock(
    strat_proxy, sett_proxy, governance, want, deployer, locker
):

    initial_bal = want.balanceOf(strat_proxy)

    ## Sleep until unlock time
    if(chain.time() < KNOWN_UNLOCK_TIME):
      chain.sleep(KNOWN_UNLOCK_TIME - chain.time() + 1)

    ## Process unlock
    strat_proxy.manualProcessExpiredLocks({"from": governance})

    assert want.balanceOf(strat_proxy) >= initial_bal + EXPECTED_AMOUNT
    assert sett_proxy.getPricePerFullShare() == 1e18 ## no increase in ppfs, just unlock


