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
def badger_tree(upgraded_strat):
    return upgraded_strat.BADGER_TREE()

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

    claim_tx = upgraded_strat.claimBribeFromConvex(spell_token, {"from": real_strategist})

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver

    assert claim_tx.events["RewardsCollected"]["amount"] > 0

def test_claim_convex_bulk_bribes(upgraded_strat, bribes_receiver, real_strategist):

    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")
    alcx_token = ERC20Upgradeable.at("0xdbdb4d16eda451d0503b854cf79d55697f90c8df")
    neutrino_token = ERC20Upgradeable.at("0x9D79d5B61De59D882ce90125b18F74af650acB93")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)
    balance_for_receiver_alcx = alcx_token.balanceOf(bribes_receiver)
    balance_for_receiver_neutrino = neutrino_token.balanceOf(bribes_receiver)

    claim_tx = upgraded_strat.claimBribesFromConvex(
        [spell_token, alcx_token, neutrino_token],
        {"from": real_strategist}
    )

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver_spell
    assert alcx_token.balanceOf(bribes_receiver) > balance_for_receiver_alcx
    assert neutrino_token.balanceOf(bribes_receiver) > balance_for_receiver_neutrino

    assert claim_tx.events["RewardsCollected"][0]["amount"] > 0


"""
NOTE: This will work only this week / until we push to live
See here for how data was found
https://github.com/oo-00/Votium/blob/e5053b45fcf3d0fa346721b758c5e97cf34cc3ec/merkle/BADGER/0002.json#L1220
"""
## NOTE: This data has to change every week as votium rewrites the merkleProof
TOKEN = "0x3472A5A71965499acd81997a54BBA8D852C6E53d"
INDEX = 162
AMOUNT = "0x6e93cdf19e6ff80000"
PROOF = [
        "0xe8b54c8216d6f973dc307be5d8771c6661161027dc3f503d00d41cc431736101",
        "0xe042cd20124dcb2cd73b5fa7faadbf2d7ed2e29228ef7e3d4513a5973472710c",
        "0x2c8a3f30a5f990eeba265716db15b8b32daa0ee9adee0107a29935ddecd29a00",
        "0x25163cf588e80f1869bc70424f9d2abcf944425bce504a45df0f634c1dbefbea",
        "0xc1e5c473eae360a8fe2ec5da321886a476aa8a181898856c88c3569f5809cf5d",
        "0x05978f187ee596396fb5c1aa5686f746bb4f87ee2ab3e717f03199f9b117a316",
        "0x4ab42f1938ae314b376fcaa55458619bb10695eddc366cf5f47cd5c1a7e311f8",
        "0x5ac451a9ea055a61c0b88482f911dd6bd5ad2b0440cea4bef3363aa0eaa43eef",
        "0x547e5952ac85e0559a8c01bd70547a0614930c0c61f7d6452fe956b7a9183232"
      ]

def test_claim_votium_bribes(upgraded_strat, badger_tree, real_strategist):
  badger_token = ERC20Upgradeable.at(TOKEN)
  badger_tree = upgraded_strat.BADGER_TREE()
  balance_for_tree = badger_token.balanceOf(badger_tree)

  claim_tx = upgraded_strat.claimBribeFromVotium(
    TOKEN,
    INDEX,
    upgraded_strat,
    AMOUNT,
    PROOF,
    {"from": real_strategist}
  )


  ## NOTE: Since it's BADGER we check balance on the tree and the event being emitted
  assert badger_token.balanceOf(badger_tree) > balance_for_tree

  assert claim_tx.events["TreeDistribution"]["token"] == badger_token
  assert claim_tx.events["TreeDistribution"]["amount"] >= 0

def test_bulk_claim_votium_bribes(upgraded_strat, badger_tree, real_strategist):
  badger_token = ERC20Upgradeable.at(TOKEN)
  balance_for_tree = badger_token.balanceOf(badger_tree)

  claim_tx = upgraded_strat.claimBribesFromVotium(
    upgraded_strat,
    [TOKEN],
    [INDEX],
    [AMOUNT],
    [PROOF],
    {"from": real_strategist}
  )

  assert badger_token.balanceOf(badger_tree) > balance_for_tree

  assert claim_tx.events["TreeDistribution"]["token"] == badger_token
  assert claim_tx.events["TreeDistribution"]["amount"] >= 0