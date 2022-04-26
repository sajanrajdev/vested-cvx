from brownie import (
    accounts,
    interface,
    Controller,
    SettV4,
    MyStrategy,
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

VOTIUM_TREE = "0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A"
CVX_EXTRA_REWARDS = "0xDecc7d761496d30F30b92Bdf764fb8803c79360D"


"""
Tests for the Bribes functonality, to be run after upgrades
These tests must be run on mainnet-fork
On separate file to avoid wasting time
"""

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

    spell_token = interface.IERC20("0x090185f2135308bad17527004364ebcc2d37e5f6")

    balance_for_receiver = spell_token.balanceOf(bribes_receiver)

    claim_tx = upgraded_strat.claimBribeFromConvex(CVX_EXTRA_REWARDS, spell_token, {"from": real_strategist})

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver

    assert claim_tx.events["RewardsCollected"]["amount"] > 0

def test_claim_convex_bulk_bribes(upgraded_strat, bribes_receiver, real_strategist):
    """
        Note: We only claim spell because rest of tokens claimableRewards is 0
    """

    spell_token = interface.IERC20("0x090185f2135308bad17527004364ebcc2d37e5f6")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)

    claim_tx = upgraded_strat.claimBribesFromConvex(
        CVX_EXTRA_REWARDS,
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
TOKEN = "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0"
INDEX = 1722
AMOUNT = "0x01f1d18726d97cd00000"
PROOF = [
    "0xc6ddc99b8a2bb8378f7b811c7281849117a87ce247f6dc92926bb546594a7490",
    "0x4f978c063490a34ede1814ecfb4432f39a685ff62df6913b2cf62eac9e5bfa55",
    "0xddf0a391c6cfbe557930b4c4ae0cf98c07b5b7d263627b8f87a7903a6a8a56f5",
    "0x33e9ebdf971adb8abe4b40b31cfad6a28c420021446481571c1e52b24d123db2",
    "0x8d69e3a795a0f9cdd79df9c147cca9dc6327757a56d6c92305791ad0c0662c22",
    "0xffba6c6611cf3a77e62a07efb0925f51dcdf2489d8dd7a89a7812d2b2466ae62",
    "0xf80b58b72d29ef8ce8b777ed7c439537427401661e84b18b2087b5c64331094a",
    "0x8dafeb699a352b4f8a8d7da68661ca5ffdd3ec1f72a66ae14a884734269aee9c",
    "0x4d1f91ffeb262db004a2f9e2567571ff0d322959d213e52987de73331190cf05",
    "0x8ab6501a2ad89b4efb6ee3fa6cc5ad69e94662b3b11ea6cb960ddab1133386bf",
    "0x3a7639bbe5f18855e6294e7abace478c8a2b9922fbb71054c7d1b7e5360c447c",
    "0x9a16c9e7a680e5d597cdf752df9ec9d25799157663d2b253e102f9cd4733f577"
]



def test_claim_votium_bribes(upgraded_strat, badger_tree, real_strategist, bribes_receiver):
  cvx_token = interface.IERC20(TOKEN)
  balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

  claim_tx = upgraded_strat.claimBribeFromVotium(
    VOTIUM_TREE,
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
  cvx_token = interface.IERC20(TOKEN)
  balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

  claim_tx = upgraded_strat.claimBribesFromVotium(
    VOTIUM_TREE,
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
    cvx_token = interface.IERC20(TOKEN)
    balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

    rando = accounts[6]
    balance_for_rando = cvx_token.balanceOf(rando)
        
    with brownie.reverts():
        claim_tx = upgraded_strat.claimBribesFromVotium(
            VOTIUM_TREE,
            upgraded_strat,
            [TOKEN],
            [INDEX],
            [AMOUNT],
            [PROOF],
            {"from": accounts[6]}
        )

RECIPIENT = "0x898111d1F4eB55025D0036568212425EE2274082"
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

    merkle = interface.IVotiumBribes(VOTIUM_TREE)

    spell_token = interface.IERC20(TOKEN)
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