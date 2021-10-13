from brownie import (
    accounts,
    interface,
    Controller,
    SettV4,
    MyStrategy,
    ERC20Upgradeable,
    Contract
)
import brownie
from brownie.network.account import Account
from config import (
    BADGER_DEV_MULTISIG,
    WANT,
    LP_COMPONENT,
    REWARD_TOKEN,
    PROTECTED_TOKENS,
    FEES,
)
from dotmap import DotMap
import pytest


"""
Tests for the Bribes functonality, to be run after upgrades
These tests must be run on mainnet-fork
On separate file to avoid wasting time
"""

SETT_ADDRESS = "0xfd05D3C7fe2924020620A8bE4961bBaA747e6305"

STRAT_ADDRESS = "0x3ff634ce65cDb8CC0D569D6d1697c41aa666cEA9"

@pytest.fixture
def vault_proxy():
    return SettV4.at(SETT_ADDRESS)

@pytest.fixture
def controller_proxy(vault_proxy):
    return Controller.at(vault_proxy.controller())

@pytest.fixture
def strat_proxy():
    return MyStrategy.at(STRAT_ADDRESS)

@pytest.fixture
def proxy_admin():
    """
     Verify by doing web3.eth.getStorageAt("STRAT_ADDRESS", int(
        0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103
    )).hex()
    """
    return Contract.from_explorer("0x20dce41acca85e8222d6861aa6d23b6c941777bf")

@pytest.fixture
def proxy_admin_gov():
    """
        Also found at proxy_admin.owner()
    """
    return accounts.at("0x21cf9b77f88adf8f8c98d7e33fe601dc57bc0893", force=True)

@pytest.fixture
def upgraded_strat(vault_proxy, controller_proxy, deployer, strat_proxy, proxy_admin, proxy_admin_gov):
    new_strat_logic = MyStrategy.deploy({"from": deployer})
    proxy_admin.upgrade(strat_proxy, new_strat_logic, {"from": proxy_admin_gov})
    return strat_proxy

@pytest.fixture
def bribes_receiver(upgraded_strat):
    return upgraded_strat.BRIBES_RECEIVER()

@pytest.fixture
def real_strategist(upgraded_strat):
    return accounts.at(upgraded_strat.strategist(), force=True)

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


## Convex Bribes tests
## https://etherscan.io/address/0x8Ed4bbf39E3080b35DA84a13A0D1A2FDcE1e0602
## Tokens are:
## SPELL: 0x090185f2135308bad17527004364ebcc2d37e5f6
## ALCX: 0xdbdb4d16eda451d0503b854cf79d55697f90c8df
## Neutrino: 0x9D79d5B61De59D882ce90125b18F74af650acB93

def test_claim_convex_single_bribe(upgraded_strat, bribes_receiver, real_strategist):

    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")

    balance_for_receiver = spell_token.balanceOf(bribes_receiver)

    upgraded_strat.claimBribeFromConvex(spell_token, {"from": real_strategist})

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver

def test_claim_convex_bulk_bribes(upgraded_strat, bribes_receiver, real_strategist):

    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")
    alcx_token = ERC20Upgradeable.at("0xdbdb4d16eda451d0503b854cf79d55697f90c8df")
    neutrino_token = ERC20Upgradeable.at("0x9D79d5B61De59D882ce90125b18F74af650acB93")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)
    balance_for_receiver_alcx = alcx_token.balanceOf(bribes_receiver)
    balance_for_receiver_neutrino = neutrino_token.balanceOf(bribes_receiver)

    upgraded_strat.claimBribesFromConvex(
        [spell_token, alcx_token, neutrino_token],
        {"from": real_strategist}
    )

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver_spell
    assert alcx_token.balanceOf(bribes_receiver) > balance_for_receiver_alcx
    assert neutrino_token.balanceOf(bribes_receiver) > balance_for_receiver_neutrino


"""
NOTE: This will work only this week / until we push to live
See here for how data was found
https://github.com/oo-00/Votium/blob/e5053b45fcf3d0fa346721b758c5e97cf34cc3ec/merkle/BADGER/0002.json#L1220
"""

TOKEN = "0x3472A5A71965499acd81997a54BBA8D852C6E53d"
INDEX = 83
AMOUNT = "0x0de0b6b3a7640000"
PROOF = [
        "0x1ae90fdb6127c7cf8c74de3c489e1218c8bc2efa9dba0d4ae127dcf85720e9f9",
        "0xea0778bf8d17dbe3347e22be9e1976d7ad265c5a3697fa2407d6d5dbd4ec1106",
        "0xe1e41af76373b4975609907edb2e8fb704db3bbd34a3630b3f2e806beae9b077",
        "0x0d08fa29561fd186c02a8344409720554295bcf196a7618bf26eb7f5cda5e5db",
        "0x227c98a62447a59091fddef2cb18be1b1d381b9c344569c2031b6f0f5ed1d3fd",
        "0xe79d45d570f91255ba88ed5adfee28fc93f2e5a040d438ea5476c495201e09b8",
        "0x989737ec30786bae1b514674726b55ec394fcdbe436d25cf65bfc9dcea9c8a57",
        "0xcedf99c49cbb5c38f212f3b9a0939674f2d4368319f6aa9edf999da744a60855",
        "0x1c4a767629e88473b4c73edf6525b0dfde8280d7b5825c8f22c1222a8be13084"
      ]

def test_claim_votium_bribes(upgraded_strat, bribes_receiver, real_strategist):
  badger_token = ERC20Upgradeable.at(TOKEN)
  balance_for_receiver_badger = badger_token.balanceOf(bribes_receiver)

  upgraded_strat.claimBribeFromVotium(
    TOKEN,
    INDEX,
    upgraded_strat,
    AMOUNT,
    PROOF,
    {"from": real_strategist}
  )

  assert badger_token.balanceOf(bribes_receiver) > balance_for_receiver_badger

def test_bulk_claim_votium_bribes(upgraded_strat, bribes_receiver, real_strategist):
  badger_token = ERC20Upgradeable.at(TOKEN)
  balance_for_receiver_badger = badger_token.balanceOf(bribes_receiver)

  upgraded_strat.claimBribesFromVotium(
    upgraded_strat,
    [TOKEN],
    [INDEX],
    [AMOUNT],
    [PROOF],
    {"from": real_strategist}
  )

  assert badger_token.balanceOf(bribes_receiver) > balance_for_receiver_badger