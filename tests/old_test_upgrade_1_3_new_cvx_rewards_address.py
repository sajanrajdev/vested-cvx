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
def real_strategist(strat_proxy):
    return accounts.at(strat_proxy.strategist(), force=True)

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def upgrade_harvest_and_claim_cvx(vault_proxy, controller_proxy, deployer, strat_proxy, proxy_admin, proxy_admin_gov, real_strategist):
    """
        OLD
        Test for the 1.3 upgrade, checks that we can upgrade and we receive new CVX reward from the new contract
    """
    new_strat_logic = MyStrategy.deploy({"from": deployer})

    bribes_receiver = strat_proxy.BRIBES_RECEIVER()
    
    assert strat_proxy.CVX_EXTRA_REWARDS() == "0x8Ed4bbf39E3080b35DA84a13A0D1A2FDcE1e0602"

    ## Setting all variables, we'll use them later
    prev_strategist = strat_proxy.strategist()
    prev_gov = strat_proxy.governance()
    prev_guardian = strat_proxy.guardian()
    prev_keeper = strat_proxy.keeper()
    prev_perFeeG = strat_proxy.performanceFeeGovernance()
    prev_perFeeS = strat_proxy.performanceFeeStrategist()
    prev_reward = strat_proxy.reward()
    prev_unit = strat_proxy.uniswap()

    prev_check_withdrawalSafetyCheck = strat_proxy.withdrawalSafetyCheck()
    prev_check_harvestOnRebalance = strat_proxy.harvestOnRebalance()
    prev_check_processLocksOnReinvest = strat_proxy.processLocksOnReinvest()
    prev_check_processLocksOnRebalance = strat_proxy.processLocksOnRebalance()

    # Deploy new logic
    proxy_admin.upgrade(strat_proxy, new_strat_logic, {"from": proxy_admin_gov})

    gov = accounts.at(strat_proxy.governance(), force=True)

    ## Checking all variables are as expected
    assert prev_strategist == strat_proxy.strategist()
    assert prev_gov == strat_proxy.governance()
    assert prev_guardian == strat_proxy.guardian()
    assert prev_keeper == strat_proxy.keeper()
    assert prev_perFeeG == strat_proxy.performanceFeeGovernance()
    assert prev_perFeeS == strat_proxy.performanceFeeStrategist()
    assert prev_reward == strat_proxy.reward()
    assert prev_unit == strat_proxy.uniswap()

    ## Checking new variables
    assert prev_check_withdrawalSafetyCheck == strat_proxy.withdrawalSafetyCheck()
    assert prev_check_harvestOnRebalance == strat_proxy.harvestOnRebalance()
    assert prev_check_processLocksOnReinvest == strat_proxy.processLocksOnReinvest()
    assert prev_check_processLocksOnRebalance == strat_proxy.processLocksOnRebalance()

    ## Verify new Addresses are setup properly
    assert strat_proxy.LOCKER() == "0xD18140b4B819b895A3dba5442F959fA44994AF50"
    assert strat_proxy.CVX_EXTRA_REWARDS() == "0xDecc7d761496d30F30b92Bdf764fb8803c79360D"
    assert strat_proxy.VOTIUM_BRIBE_CLAIMER() == "0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A"
    assert strat_proxy.BRIBES_RECEIVER() == "0x6F76C6A1059093E21D8B1C13C4e20D8335e2909F"


    ## Also run all ordinary operation just because
    with brownie.reverts("no op"):
        ## Tend successfully fails as we hardcoded a revert
        strat_proxy.tend({"from": gov})
    with brownie.reverts("You have to wait for unlock or have to manually rebalance out of it"):
        ## Withdraw All successfully fails as we are locked
        controller_proxy.withdrawAll(vault_proxy.token(), {"from": accounts.at(controller_proxy.governance(), force=True)})
    
    vault_proxy.earn({"from": gov})

    strat_proxy.harvest({"from": gov})

    ## Claim Rewards
    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")
    badger_token = ERC20Upgradeable.at("0x3472A5A71965499acd81997a54BBA8D852C6E53d")
    meta_token = ERC20Upgradeable.at("0xa3BeD4E1c75D00fa6f4E5E6922DB7261B5E9AcD2")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)
    balance_for_receiver_badger = badger_token.balanceOf(bribes_receiver)
    balance_for_receiver_meta = meta_token.balanceOf(bribes_receiver)

    claim_tx = strat_proxy.claimBribesFromConvex(
        [spell_token, badger_token, meta_token],
        {"from": real_strategist}
    )

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver_spell
    ## NOTE: These 2 tokens will not increase as it seems like we're only entitled to spell bribes
    assert badger_token.balanceOf(bribes_receiver) > balance_for_receiver_badger
    assert meta_token.balanceOf(bribes_receiver) > balance_for_receiver_meta

    assert claim_tx.events["RewardsCollected"][0]["amount"] > 0
