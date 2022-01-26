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


TOKEN = "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B"
INDEX = 780
AMOUNT = "0x6e4a3cd203a5a40000"
PROOF = [
    "0x6b6b79fd81fce07f4f2dbd93a6c26f29b418c452af2b35b800a17fe2906fbb19",
    "0x76100f93f7960e8719a6d1795ab2aae9d0fc1073e0bec5e52f5e307727280f0d",
    "0xfc68f3a8e335b78b09f13894018bd9412c3baedbb3b822037a966017ab70e0d3",
    "0x89e506f7a982587729051ddb24e8e8c45ba563baf7a6dde1f34de656e3fdd483",
    "0xf8596e0ddcfc1280e13b9ce756ba72b7ab68fddc7872edc459eb8f2d06c6aa3a",
    "0x362e2ec07ec33976ec4064ac054babc8c475552e117091dfd5a24f1031d8f9a4",
    "0xecc236a28e9b502faec1edaf31e479acc089930db5d97b2334be45e3a5cf1f0f",
    "0x2695ba7f73a8b379dc10339640a02187b96964b48e9ffcb2788fab7da447c0e6",
    "0xfa6d969f1c23237b58a5f963403e5798ec2d09947f3cd03d705c1adeb739886e",
    "0x695dd510ed78ee767e5192b581d8d91faaae71b0916743ca4bdeeac292715a79",
    "0x5a532a387db2c517b979fcf239818f8ba0e1ebad8b3ee6483693cde39595be60",
    "0x342bc7e70d4d33d60efd183eeabf86d5bbc5a83bcbae76cddb2aca71d3057c6f"
]

def test_upgrade_harvest_and_claim_cvx(vault_proxy, controller_proxy, deployer, strat_proxy, proxy_admin, proxy_admin_gov, real_strategist):
    """
        Test for the 1.4 upgrade, checks that we can upgrade and we receive new CVX reward from the new contract
    """
    new_strat_logic = MyStrategy.deploy({"from": deployer})

    bribes_receiver = strat_proxy.BRIBES_RECEIVER()
    
    assert strat_proxy.CVX_EXTRA_REWARDS() == "0xDecc7d761496d30F30b92Bdf764fb8803c79360D"

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

    ## Claim Rewards Convex Rewards
    spell_token = ERC20Upgradeable.at("0x090185f2135308bad17527004364ebcc2d37e5f6")

    balance_for_receiver_spell = spell_token.balanceOf(bribes_receiver)

    claim_tx = strat_proxy.claimBribesFromConvex(
        [spell_token],
        {"from": real_strategist}
    )

    assert spell_token.balanceOf(bribes_receiver) > balance_for_receiver_spell

    assert claim_tx.events["RewardsCollected"][0]["amount"] > 0


    ## Claim Bribes Votium

    cvx_token = ERC20Upgradeable.at(TOKEN)
    balance_for_receiver_cvx = cvx_token.balanceOf(bribes_receiver)

    claim_tx = strat_proxy.claimBribeFromVotium(
        TOKEN,
        INDEX,
        strat_proxy,
        AMOUNT,
        PROOF,
        {"from": real_strategist}
    )


    ## NOTE: Since it's BADGER we check balance on the tree and the event being emitted
    assert cvx_token.balanceOf(bribes_receiver) > balance_for_receiver_cvx

    assert claim_tx.events["RewardsCollected"]["token"] == cvx_token
    assert claim_tx.events["RewardsCollected"]["amount"] >= 0
