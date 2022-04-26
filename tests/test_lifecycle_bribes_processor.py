import pytest
import brownie
from brownie import *
from helpers.constants import MaxUint256
from eth_utils import encode_hex
from helpers.constants import EmptyBytes32

"""
  Upgrade Live Strategy
  And test if it works
"""



@pytest.fixture
def processor(upgraded_strat):
  return BribesProcessor.at(upgraded_strat.BRIBES_PROCESSOR())

@pytest.fixture
def manager(processor):
  return accounts.at(processor.manager(), force=True)

"""
  TODO: Claim Bribes
  Check that timer is properly set
  
  Wait 14 days and show that you can sweep

  Check fee processing and that tokens are there.

  Done.
"""

@pytest.fixture
def fake_bribes(test_token, test_whale, test_token_amount):
  """
    Contract that returns XYZ amount of Token
  """
  c = FakeBribeClaimer.deploy({"from": a[0]})
  test_token.transfer(c, test_token_amount, {"from": test_whale})

  return c

def test_lifecycle_processor_basic_claim(bribes_processor, fake_bribes, test_token, test_token_amount, upgraded_strat, real_strategist):
  ## Verify Transfer does happen
  initial_receiver_bal = test_token.balanceOf(bribes_processor)
  initial_processor_timestamp = bribes_processor.lastBribeAction()

  upgraded_strat.claimBribeFromConvex(fake_bribes, test_token, {"from": real_strategist})

  ## Verify timestamp did change
  assert test_token.balanceOf(bribes_processor) == initial_receiver_bal + test_token_amount
  assert bribes_processor.lastBribeAction() > initial_processor_timestamp


def test_lifecycle_processor_list_claim(bribes_processor, fake_bribes, test_token, test_token_amount, upgraded_strat, real_strategist):
  ## Verify Transfer does happen
  initial_receiver_bal = test_token.balanceOf(bribes_processor)
  initial_processor_timestamp = bribes_processor.lastBribeAction()

  upgraded_strat.claimBribesFromConvex(fake_bribes, [test_token], {"from": real_strategist})

  ## Verify timestamp did change
  assert test_token.balanceOf(bribes_processor) == initial_receiver_bal + test_token_amount
  assert bribes_processor.lastBribeAction() > initial_processor_timestamp

def test_lifecycle_processor_basic_votium(bribes_processor, fake_bribes, test_token, test_token_amount, upgraded_strat, real_strategist):
  ## Verify Transfer does happen
  initial_receiver_bal = test_token.balanceOf(bribes_processor)
  initial_processor_timestamp = bribes_processor.lastBribeAction()

  upgraded_strat.claimBribeFromVotium(fake_bribes, test_token, 1, upgraded_strat, 123, [EmptyBytes32], {"from": real_strategist})

  ## Verify timestamp did change
  assert test_token.balanceOf(bribes_processor) == initial_receiver_bal + test_token_amount
  assert bribes_processor.lastBribeAction() > initial_processor_timestamp


def test_lifecycle_processor_list_votium(bribes_processor, fake_bribes, test_token, test_token_amount, upgraded_strat, real_strategist):
  ## Verify Transfer does happen
  initial_receiver_bal = test_token.balanceOf(bribes_processor)
  initial_processor_timestamp = bribes_processor.lastBribeAction()

  upgraded_strat.claimBribesFromVotium(fake_bribes, upgraded_strat, [test_token], [123], [123], [[EmptyBytes32]], {"from": real_strategist})

  ## Verify timestamp did change
  assert test_token.balanceOf(bribes_processor) == initial_receiver_bal + test_token_amount
  assert bribes_processor.lastBribeAction() > initial_processor_timestamp
