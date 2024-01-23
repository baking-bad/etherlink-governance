from tests.base import BaseTestCase
from tests.helpers.utility import pkh

class GovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_governance()

        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        with self.raisesMichelsonError("NO_VOTING_POWER"):
            governance.using(no_baker).new_proposal(pkh(no_baker), kernel_hash, 'abc.com').send()