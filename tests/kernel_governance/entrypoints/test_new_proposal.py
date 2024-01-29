from tests.base import BaseTestCase
from tests.helpers.contracts.kernel_governance import PROMOTION_PERIOD
from tests.helpers.utility import pkh, pack

class KernelGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        with self.raisesMichelsonError("XTZ_IN_TRANSACTION_DISALLOWED"):
            governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').with_amount(1).send()

    def test_should_fail_if_sender_is_not_key_hash_owner(self) -> None:
        no_baker = self.bootstrap_no_baker()
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        with self.raisesMichelsonError("SENDER_NOT_KEY_HASH_OWNER"):
            governance.using(no_baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_kernel_governance()

        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        with self.raisesMichelsonError("NO_VOTING_POWER"):
            governance.using(no_baker).new_proposal(pkh(no_baker), kernel_hash, 'abc.com').send()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 2,
            'min_proposal_quorum': 20 # 1 bakers out of 5 voted
        })
        
         # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(pkh(baker), '0101010101010101010101010101010101010101', 'abc.com').send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        context = governance.get_voting_context()
        assert context['voting_context']['period_index'] == 1
        assert context['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        kernel_hash = bytes.fromhex('0202020202020202020202020202020202020202')
        with self.raisesMichelsonError("NOT_PROPOSAL_PERIOD"):
            governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 2
        })
        
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(pkh(baker), '0101010101010101010101010101010101010101', 'abc.com').send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(pkh(baker), '0202020202020202020202020202020202020202', 'abc.com').send()
        self.bake_block()

        with self.raisesMichelsonError("PROPOSAL_LIMIT_EXCEEDED"):
            governance.using(baker).new_proposal(pkh(baker), '0303030303030303030303030303030303030303', 'abc.com').send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 2
        })
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()
        self.bake_block()

        with self.raisesMichelsonError("PROPOSAL_ALREADY_CREATED"):
            governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 2
        })

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 0
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()
        self.bake_block()

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert list(context['voting_context']['proposals'].values())[0] == {
            'payload': pack(kernel_hash, 'bytes')[6:], 
            'url': 'abc.com', 
            'proposer': pkh(baker), 
            'voters': [pkh(baker)], 
            'up_votes_power': 4000000000000
        }