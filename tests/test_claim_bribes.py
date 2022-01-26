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



def test_random_cant_claim(upgraded_strat, badger_tree, real_strategist, bribes_receiver):
    """
        NOTE: We removed ability for randoms to call so this test checks for reverts
    """
    cvx_token = ERC20Upgradeable.at(TOKEN)
    balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

    rando = accounts[6]
    balance_for_rando = cvx_token.balanceOf(rando)
        
    with brownie.reverts():
        claim_tx = upgraded_strat.claimBribesFromVotium(
            upgraded_strat,
            [TOKEN],
            [INDEX],
            [AMOUNT],
            [PROOF],
            {"from": accounts[6]}
        )

RECIPIENT = "0x3ff634ce65cDb8CC0D569D6d1697c41aa666cEA9"
TOKEN = "0x090185f2135308bad17527004364ebcc2d37e5f6"
INDEX = 701
AMOUNT = "0x03329014ceb09a00000000"
PROOF = [
      "0x5a4981be6a1c84fd17cf5f0f4e00ba5567c3ac813d8a5fdf7dc60ce048483ff5",
      "0x5c6093797cf0a804bf747bc9aae7c20f1206c37e4bee7df9d7102c5c4c02f5ef",
      "0xe0e754041218abb7b52dcc0bf5d5b75dcba1be8e3ca81f8e009787a7ec0893f3",
      "0x7e0c1a7b8e80e8939d272912f6cb2bbf3bb2b414d66331b4a73865e5d54b320f",
      "0x80c883e31fc96a7c5656942d03ace3552896f99c73d5428a9be94fc32df17975",
      "0x6064e5d02d3b2fb3860b362af1c555d62a0e07261b50f3e964d0c2bba2fe9b50",
      "0xa79aeac5d41987c280948c631323a6b73ab80510c9d2a44ad9fa668c935545a9",
      "0xa759fa153d807e4e2519ecf881d064276aa13ac823e8f02f06cbc0d028bf25a7",
      "0x0ef4d7dcbca4db560498d6362633ad75ffd73e2cae850e37feeb1f2a8d58aa92",
      "0xf8a2e6870a3d35dff77b1c1f2af4226e7fcdc486bae82517cf89bc4d88f96c3f",
      "0xe2516c2950da5e6e28e774eac55653e40d7d435a539ea6c4fa9eff61d3d7e290",
      "0x1cf4c12ecc23fd268dc8839358619c1c7bf3daeaaa60469e3e5d8a231515f218"
    ]

def test_if_griefed_we_can_sweep(upgraded_strat, badger_tree, real_strategist, bribes_receiver):
    """
       People can grief by claiming for us, we can sweep to avoid probs
       Only token that can get stuck is CVX, in that case it's gonna increase ppfs but be safe
    """

    merkle = interface.IVotiumBribes(upgraded_strat.VOTIUM_BRIBE_CLAIMER())

    spell_token = ERC20Upgradeable.at(TOKEN)
    balance_for_receiver = spell_token.balanceOf(bribes_receiver)

    rando = accounts[6]
    balance_for_rando = spell_token.balanceOf(rando)

    balance_for_strategy = spell_token.balanceOf(upgraded_strat)

    ## Rando claims spell token for strat, breaking the cliam flow
    claim_tx = merkle.claim(spell_token, INDEX, RECIPIENT, AMOUNT, PROOF, {"from": rando})

    assert spell_token.balanceOf(upgraded_strat) > balance_for_strategy

    ## We "rescue" by using the sweep function
    upgraded_strat.sweepRewards([spell_token], {"from": real_strategist})

    assert spell_token.balanceOf(upgraded_strat) == 0 ## Spell has moved
    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver ## Receiver got them