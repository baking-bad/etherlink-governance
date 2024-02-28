from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import YAY_VOTE
from tests.helpers.errors import (
    LAST_WINNER_PAYLOAD_NOT_FOUND,
    XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_ADDRESS
import re

class KernelGovernanceTriggerKernelUpgradeTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).trigger_kernel_upgrade(DEFAULT_ADDRESS).with_amount(1).send()

    def test_should_fail_if_there_is_no_last_winner_payload(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(LAST_WINNER_PAYLOAD_NOT_FOUND):
            governance.using(baker).trigger_kernel_upgrade(DEFAULT_ADDRESS).send()

    def test_should_send_last_winner_payload_to_rollup(self) -> None:
        baker = self.bootstrap_baker()
        rollup_mock = self.deploy_rollup_mock()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20,
            'promotion_quorum': 20,
            'promotion_supermajority': 20,
        })

        kernel_root_hash = bytes.fromhex('020202020202020202020202020202020202020202020202020202020202020202')
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(kernel_root_hash).send()
        self.bake_blocks(2)

        # Period index: 1. Block: 2 of 2
        governance.using(baker).vote(YAY_VOTE).send()
        self.bake_blocks(2)

        payload_pattern = rf'^EBA1{kernel_root_hash.hex()}88[\da-f]{{16}}$'
        assert not re.match(payload_pattern, rollup_mock.contract.storage().hex(), re.IGNORECASE)

        governance.using(baker).trigger_kernel_upgrade(rollup_mock.contract.address).send()
        self.bake_block()
        assert re.match(payload_pattern, rollup_mock.contract.storage().hex(), re.IGNORECASE)