import pytest
import brownie
from brownie import *
from helpers.constants import MaxUint256
from eth_utils import (
    keccak,
)

"""
  TODO: Put your tests here to prove the strat is good!
  See test_harvest_flow, for the basic tests
  See test_strategy_permissions, for tests at the permissions level
"""


@pytest.fixture
def setup_strat(deployer, sett, strategy, want):
    """
    Convenience fixture that depoists and harvests for us
    """
    # Setup
    startingBalance = want.balanceOf(deployer)

    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    # End Setup

    # Deposit
    assert want.balanceOf(sett) == 0

    want.approve(sett, MaxUint256, {"from": deployer})
    sett.deposit(depositAmount, {"from": deployer})

    available = sett.available()
    assert available > 0

    sett.earn({"from": deployer})

    chain.sleep(10000 * 13)  # Mine so we get some interest
    return strategy


def test_if_not_wait_withdrawal_reverts(setup_strat, sett, deployer):
    ## Try to withdraw all, fail because locked
    initial_dep = sett.balanceOf(deployer)

    with brownie.reverts():
        sett.withdraw(initial_dep, {"from": deployer})


def test_if_change_min_some_can_be_withdraw_easy(setup_strat, sett, deployer, want):

    initial_b = want.balanceOf(deployer)
    ## TODO / CHECK This is the ideal math but it seems to revert on me
    ## min = (sett.max() - sett.min() - 1) * sett.balanceOf(deployer) / 10000
    min = (sett.max() - sett.min() - 1) * sett.balanceOf(deployer) / 10000

    sett.withdraw(min * 0.70, {"from": deployer})

    assert (
        want.balanceOf(deployer) > initial_b
    )  ## You can withdraw as long as it's less than min


def test_wait_for_all_locks_can_withdraw_easy(
    setup_strat, deployer, sett, strategy, want, locker
):
    ## Strategy has funds and they are locked
    ## Wait a bunch and see if you can withdraw all

    initial_dep = sett.balanceOf(deployer)

    ## Wait to unlock
    chain.sleep(86400 * 250)  # 250 days so lock expires

    ## Try to withdraw all
    sett.withdraw(initial_dep, {"from": deployer})

    assert want.balanceOf(deployer) > initial_dep  ## Assert that we made some money
    ## If this passes, implicitly it means the lock was expire and we were able to withdraw


def test_after_deposit_proxy_has_more_funds(
    locker, deployer, sett, strategy, want, staking
):
    """
    We have to check that Strategy Proy
    """
    proxy = locker.stakingProxy()

    initial_in_proxy = staking.balanceOf(proxy)

    # Setup
    startingBalance = want.balanceOf(deployer)
    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    # End Setup
    # Deposit
    assert want.balanceOf(sett) == 0

    want.approve(sett, MaxUint256, {"from": deployer})
    sett.deposit(depositAmount, {"from": deployer})

    available = sett.available()
    assert available > 0

    sett.earn({"from": deployer})

    chain.sleep(10000 * 13)  # Mine so we get some interest

    ## TEST: Did the proxy get more want?
    assert staking.balanceOf(proxy) > initial_in_proxy


def test_delegation_was_correct(delegation_registry, strategy):
    target_delegate = strategy.DELEGATE()
    status = delegation_registry.delegation(strategy, "cvx.eth")

    assert status == target_delegate
