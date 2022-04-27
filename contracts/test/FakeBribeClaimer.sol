// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;


import "../../interfaces/cvx/ICVXBribes.sol";
import "../../interfaces/cvx/IVotiumBribes.sol";
import "../../deps/@openzeppelin/contracts/token/ERC20/SafeERC20.sol";


/// @dev Fake Bribes contract to facilitate basic testing
contract FakeBribeClaimer is IVotiumBribes, ICVXBribes {
  using SafeERC20 for IERC20;
    function getReward(address _account, address _token) external override {
      IERC20(_token).safeTransfer(_account, IERC20(_token).balanceOf(address(this)));
    }
    function getRewards(address _account, address[] calldata _tokens) external override {
      address _token = _tokens[0];
      IERC20(_token).safeTransfer(_account, IERC20(_token).balanceOf(address(this)));
    }

    function claimMulti(address account, claimParam[] calldata claims) external override {
      address token = claims[0].token;
      IERC20(token).safeTransfer(account, IERC20(token).balanceOf(address(this)));
    }
    function claim(address token, uint256 index, address account, uint256 amount, bytes32[] calldata merkleProof) external override {
        IERC20(token).safeTransfer(account, IERC20(token).balanceOf(address(this)));
    }
}