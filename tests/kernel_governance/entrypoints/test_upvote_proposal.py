from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, PROPOSAL_PERIOD
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PROPOSAL_ALREADY_UPVOTED, 
    UPVOTING_LIMIT_EXCEEDED, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER

class KernelGovernanceUpvoteProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).upvote_proposal(kernel_root_hash).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_kernel_governance()

        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).upvote_proposal(kernel_root_hash).send()

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
        
        kernel_root_hash = bytes.fromhex('020202020202020202020202020202020202020202020202020202020202020202')
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(kernel_root_hash).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).upvote_proposal(kernel_root_hash).send()


    def test_should_fail_if_upvoting_limit_is_exceeded(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 7
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 7,
            'upvoting_limit': 2
        })
        
        kernel_root_hash1 = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        # Period index: 0. Block: 2 of 7
        governance.using(baker1).new_proposal(kernel_root_hash1).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 7
        kernel_root_hash2 = bytes.fromhex('020202020202020202020202020202020202020202020202020202020202020202')
        governance.using(baker1).new_proposal(kernel_root_hash2).send()
        self.bake_block()
        # Period index: 0. Block: 4 of 7
        kernel_root_hash3 = bytes.fromhex('030303030303030303030303030303030303030303030303030303030303030303')
        governance.using(baker2).new_proposal(kernel_root_hash3).send()
        self.bake_block()
        # Period index: 0. Block: 5 of 7
        governance.using(baker3).upvote_proposal(kernel_root_hash1).send()
        self.bake_block()
        # Period index: 0. Block: 6 of 7
        governance.using(baker3).upvote_proposal(kernel_root_hash2).send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker3).upvote_proposal(kernel_root_hash3).send()


    def test_should_fail_if_proposal_already_upvoted_by_proposer(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        kernel_root_hash = '010101010101010101010101010101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(kernel_root_hash).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(kernel_root_hash).send()

    def test_should_fail_if_proposal_already_upvoted_by_another_baker(self) -> None:
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
        
        kernel_root_hash = '010101010101010101010101010101010101010101010101010101010101010101'
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(kernel_root_hash).send()
        self.bake_block()

        # Period index: 0. Block: 2 of 5
        governance.using(baker2).upvote_proposal(kernel_root_hash).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker2).upvote_proposal(kernel_root_hash).send()

    def test_should_upvote_proposal_with_correct_parameters(self) -> None:
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

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }
        
        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(kernel_root_hash).send()
        self.bake_block()

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 2 of 5
        governance.using(baker2).upvote_proposal(kernel_root_hash).send()
        self.bake_block()

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER * 2,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }