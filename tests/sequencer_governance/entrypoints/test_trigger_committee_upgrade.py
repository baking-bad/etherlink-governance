from tests.base import BaseTestCase
from tests.helpers.errors import (
    LAST_WINNER_PAYLOAD_NOT_FOUND,
    XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_ADDRESS

class CommitteeGovernanceTriggerCommitteeUpgradeTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()

        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).trigger_committee_upgrade(DEFAULT_ADDRESS).with_amount(1).send()

    def test_should_fail_if_there_is_no_last_winner_payload(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(LAST_WINNER_PAYLOAD_NOT_FOUND):
            governance.using(baker).trigger_kernel_upgrade(DEFAULT_ADDRESS).send()
