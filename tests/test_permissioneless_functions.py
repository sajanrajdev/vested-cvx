"""
  Set of tests for new functions that are going to eventually be made permissioneless
  Extra attention needs to be placed here for economic exploits
  If you have thoughts, reach out to alex@badger.finance

  Testing:
    - Skim
  Todo: 
    - Votium and Convex Claiming (not opened as of now)
"""

import pytest
import brownie
from brownie import *
from helpers.constants import MaxUint256
from eth_utils import encode_hex

def test_manual_skim_after_donation(setup_strat, vault, want, deployer):
  to_donate = want.balanceOf(deployer) // 2

  initial_ppfs = vault.getPricePerFullShare()

  assert initial_ppfs == 1e18 ## Always has been

  initial_balance = setup_strat.balanceOf()

  want.transfer(setup_strat, to_donate, {"from": deployer})

  after_donation_balance = setup_strat.balanceOf()

  after_ppfs = vault.getPricePerFullShare()

  assert after_donation_balance > initial_balance
  assert after_ppfs > initial_ppfs

  ## Skim here
  bribes_receiver = setup_strat.BRIBES_RECEIVER()
  before_balance_receiver = want.balanceOf(bribes_receiver)

  setup_strat.skim({"from": deployer})

  ## Balance of receiver has increased exactly by donation amount
  assert to_donate == want.balanceOf(bribes_receiver) - before_balance_receiver
  assert to_donate == (after_donation_balance - initial_balance)

  assert vault.getPricePerFullShare() == 1e18 ## Ppfs is back to expected



  

