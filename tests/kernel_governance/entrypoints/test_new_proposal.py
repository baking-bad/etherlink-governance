from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, YAY_VOTE
from tests.helpers.errors import (
    INCORRECT_PREIMAGE_HASH_SIZE, NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PAYLOAD_SAME_AS_LAST_WINNER,
    PROPOSAL_ALREADY_CREATED, PROPOSER_NOT_ALLOWED, UPVOTING_LIMIT_EXCEEDED, 
    XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, pack_preimage_hash, pkh

class KernelGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_preimage_hash_has_incorrect_size(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(INCORRECT_PREIMAGE_HASH_SIZE):
            governance.using(baker).new_proposal(bytes.fromhex('009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606a')).send()
        with self.raisesMichelsonError(INCORRECT_PREIMAGE_HASH_SIZE):
            governance.using(baker).new_proposal(bytes.fromhex('009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abcde')).send()
        governance.using(baker).new_proposal(bytes.fromhex('009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abc')).send()

    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).new_proposal(preimage_hash).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_kernel_governance()

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).new_proposal(preimage_hash).send()

    def test_should_fail_payload_same_as_last_winner(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20, # 1 bakers out of 5 voted
            'promotion_quorum': 20, # 1 bakers out of 5 voted
            'promotion_supermajority': 50, # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker).new_proposal(preimage_hash).send()
        self.bake_blocks(2)

        # Period index: 1. Block: 1 of 2
        governance.using(baker).vote(YAY_VOTE).send()
        self.bake_blocks(2)

        # Period index: 3. Block: 1 of 2
        with self.raisesMichelsonError(PAYLOAD_SAME_AS_LAST_WINNER):
            governance.using(baker).new_proposal(preimage_hash).send()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20 # 1 bakers out of 5 voted
        })
        
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal('010101010101010101010101010101010101010101010101010101010101010101').send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        preimage_hash = bytes.fromhex('020202020202020202020202020202020202020202020202020202020202020202')
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).new_proposal(preimage_hash).send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal('010101010101010101010101010101010101010101010101010101010101010101').send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal('020202020202020202020202020202020202020202020202020202020202020202').send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker).new_proposal('030303030303030303030303030303030303030303030303030303030303030303').send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        preimage_hash = '010101010101010101010101010101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(preimage_hash).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(preimage_hash).send()

    def test_should_fail_if_proposer_is_not_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        disallowed_baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance(custom_config={
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        with self.raisesMichelsonError(PROPOSER_NOT_ALLOWED):
            governance.using(disallowed_baker).new_proposal(preimage_hash).send()

    def test_should_not_fail_if_allowed_proposers_list_is_empty(self) -> None:
        disallowed_baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance(custom_config={
            'allowed_proposers': []
        })

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(disallowed_baker).new_proposal(preimage_hash).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_not_fail_if_proposer_is_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance(custom_config={
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(allowed_baker).new_proposal(preimage_hash).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_not_fail_if_no_baker_is_in_the_allowed_proposers_list(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_kernel_governance(custom_config={
            'allowed_proposers': [pkh(no_baker)]
        })

        preimage_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(no_baker).new_proposal(preimage_hash).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        
        preimage_hash1 = '010101010101010101010101010101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(preimage_hash1).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert list(state['voting_context']['proposal_period']['proposals'].values())[0] == {
            'payload': pack_preimage_hash(preimage_hash1), 
            'proposer': pkh(baker1), 
            'votes': {
                pkh(baker1): DEFAULT_VOTING_POWER
            },
        }


        preimage_hash2 = '020202020202020202020202020202020202020202020202020202020202020202'
        # Period index: 0. Block: 2 of 5
        governance.using(baker2).new_proposal(preimage_hash2).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 2
        assert list(state['voting_context']['proposal_period']['proposals'].values())[0] == {
            'payload': pack_preimage_hash(preimage_hash1), 
            'proposer': pkh(baker1), 
            'votes': {
                pkh(baker1): DEFAULT_VOTING_POWER
            },
        }
        assert list(state['voting_context']['proposal_period']['proposals'].values())[1] == {
            'payload': pack_preimage_hash(preimage_hash2), 
            'proposer': pkh(baker2), 
            'votes': {
                pkh(baker2): DEFAULT_VOTING_POWER
            },
        }