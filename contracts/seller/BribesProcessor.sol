// SPDX-License-Identifier: MIT
pragma solidity 0.8.10;

import {VotiumBribesProcessor} from "@seller/contracts/VotiumBribesProcessor.sol";

contract BribesProcessor is VotiumBribesProcessor {
  /// Using inheritance to import release from other brownie project
  /// DO NOT CHANGE THIS
  /// Chanding this file breaks trust in the code (untested)

  /// @notice We do need the constructor
  constructor(address _pricer) VotiumBribesProcessor(_pricer) {}
}