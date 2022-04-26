import pytest
import brownie
from brownie import *
from helpers.constants import MaxUint256
from eth_utils import encode_hex

"""
  TODO:
  Upgrade Live Strategy
  And test if it works
"""


@pytest.fixture
def pricer(deployer):
  return OnChainPricer.deploy({"from": deployer})


@pytest.fixture
def processor(pricer, deployer):
  return BribesProcessor.deploy(pricer, {"from": deployer})

@pytest.fixture
def manager(deployer):
  return deployer

"""
  TODO: Claim Bribes
  Check that timer is properly set
  
  Wait 14 days and show that you can sweep

  Check fee processing and that tokens are there.

  Done.
"""
