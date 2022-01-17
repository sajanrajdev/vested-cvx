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
    """
        Note: We only claim spell because rest of tokens claimableRewards is 0
    """

    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)

    claim_tx = upgraded_strat.claimBribesFromConvex(
        [spell_token],
        {"from": real_strategist}
    )

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver_spell

    assert claim_tx.events["RewardsCollected"][0]["amount"] > 0


"""
NOTE: This will work only this week / until we push to live
See here for how data was found
https://github.com/oo-00/Votium/blob/e5053b45fcf3d0fa346721b758c5e97cf34cc3ec/merkle/BADGER/0002.json#L1220
"""
## NOTE: This data has to change every week as votium rewrites the merkleProof
TOKEN = "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B"
INDEX = 684
AMOUNT = "0x6e4a3cd203a5a40000"
PROOF = [
    "0xde24992959a35e41f92dc070000fb59ade0b47f2399b2cbe7ec0126accc9f832",
    "0xe965287182073f2db7f8507458c9a1e168200f7973c155f5432e49dc51d80ed2",
    "0x53fba95706bb8bcfeb337fffb943c4ea708425185e2931139fdfe0e3f96ae49a",
    "0x9817ff39ca612d9b62f61f8e266df6a8d67b5406e339be58dd832e324851479e",
    "0x9fc0b7dc83afc55158b60d5709091348c4bc6f9a5263af5d42c5e70437a6db9e",
    "0xcbff70570ca71e83dbd2bdbd254c916a629092a73fd148675f55fdfb1ae85c4d",
    "0x0f53cd12926a48df89913df901b24def5d7b74f90b1e862f0103b575fcb7b0d2",
    "0x78266a424a8faf8964c0ad8ef984a56bb23daa585ce45ce549c72891f67c5619",
    "0x0395908c13baf6cf4dfb9ddba61bc7e02567fc186a4f8243ac970af4c290c634",
    "0x93fe0d6bdabadd863667aaa36cdbd1c48483b71ef903088ac2fca69964f1291e",
    "0x92313245368194a1e13309d50a3b382ea5185547fddd2651159a85936c8a7182"
]

def test_claim_votium_bribes(upgraded_strat, badger_tree, real_strategist, bribes_receiver):
  cvx_token = ERC20Upgradeable.at(TOKEN)
  balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

  claim_tx = upgraded_strat.claimBribeFromVotium(
    TOKEN,
    INDEX,
    upgraded_strat,
    AMOUNT,
    PROOF,
    {"from": real_strategist}
  )


  ## NOTE: Since it's BADGER we check balance on the tree and the event being emitted
  assert cvx_token.balanceOf(bribes_receiver) > balance_for_receiver_cvx

  assert claim_tx.events["RewardsCollected"]["token"] == cvx_token
  assert claim_tx.events["RewardsCollected"]["amount"] >= 0

def test_bulk_claim_votium_bribes(upgraded_strat, badger_tree, real_strategist, bribes_receiver):
  cvx_token = ERC20Upgradeable.at(TOKEN)
  balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

  claim_tx = upgraded_strat.claimBribesFromVotium(
    upgraded_strat,
    [TOKEN],
    [INDEX],
    [AMOUNT],
    [PROOF],
    {"from": real_strategist}
  )

  assert cvx_token.balanceOf(bribes_receiver) > balance_for_receiver_cvx

  assert claim_tx.events["RewardsCollected"]["token"] == cvx_token
  assert claim_tx.events["RewardsCollected"]["amount"] >= 0