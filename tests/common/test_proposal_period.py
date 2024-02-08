from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROPOSAL_PERIOD, PROMOTION_PERIOD
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER, pack_kernel_hash, pkh

class KernelGovernanceProposalPeriodTestCase(BaseTestCase):
    def test_should_reset_proposals_when_no_proposals(self) -> None:
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3
        })
        assert self.get_current_level() == governance_started_at_level

        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()
        # Period index: 0. Block: 2 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None
        
        self.bake_block()
        # Period index: 0. Block: 3 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()
        # Period index: 1. Block: 1 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()
        # Period index: 1. Block: 2 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_blocks(10)
        # Period index: 1. Block: 2 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 4
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

    def test_should_reset_proposals_when_period_is_finished_with_no_votes_except_proposer(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 40 # 1 baker out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 2
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker).new_proposal(pkh(baker), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == {
            'finished_at_period_index': 1, 
            'proposal_period': {
                'proposals': {
                    b'\xfa\xa8X\xa1UbF>3\xd0\xd7\xd4x\xb5J*\xe9\xcc\xfe\xa0g\x8cy#zs\xfce\x96\x90\xe6I': {
                        'payload': pack_kernel_hash(kernel_hash), 
                        'proposer': pkh(baker), 
                        'voters': [pkh(baker)], 
                        'upvotes_power': DEFAULT_VOTING_POWER
                    },
                },
                'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
            },
            'promotion_period': None, 
            'winner_payload': None
        }
    
    def test_should_reset_proposals_when_period_is_finished_with_not_enough_votes(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 60 # 2 bakers out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == {
            'finished_at_period_index': 1, 
            'proposal_period': {
                'proposals': {
                    b'\xfa\xa8X\xa1UbF>3\xd0\xd7\xd4x\xb5J*\xe9\xcc\xfe\xa0g\x8cy#zs\xfce\x96\x90\xe6I': {
                        'payload': pack_kernel_hash(kernel_hash), 
                        'proposer': pkh(baker1), 
                        'voters': [pkh(baker2), pkh(baker1)], 
                        'upvotes_power': DEFAULT_VOTING_POWER * 2
                    },
                },
                'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
            },
            'promotion_period': None, 
            'winner_payload': None
        }

    def test_should_reset_proposals_when_period_is_finished_with_2_winners(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 bakers out of 5 will vote for each proposal
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_hash1 = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash1).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        # Period index: 0. Block: 3 of 3
        kernel_hash2 = bytes.fromhex('0202020202020202020202020202020202020202')
        governance.using(baker2).new_proposal(pkh(baker2), kernel_hash2).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 2
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None
        
        self.bake_block()

        # Period index: 1. Block: 1 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == {
            'finished_at_period_index': 1, 
            'proposal_period': {
                'proposals': {
                    b'?\x0b\xfd\xe2*9\xb7\xd2\x9c\xfc\x1f\x13\x9f\xdbuy\xec\xf6\xc9+\\\x16L&\xbdK\xd7\xce\xe4\xf3\xa7\x9b': {
                        'payload': pack_kernel_hash(kernel_hash2), 
                        'proposer': pkh(baker2), 
                        'voters': [pkh(baker2)], 
                        'upvotes_power': DEFAULT_VOTING_POWER
                    },
                    b'\xfa\xa8X\xa1UbF>3\xd0\xd7\xd4x\xb5J*\xe9\xcc\xfe\xa0g\x8cy#zs\xfce\x96\x90\xe6I': {
                        'payload': pack_kernel_hash(kernel_hash1), 
                        'proposer': pkh(baker1), 
                        'voters': [pkh(baker1)], 
                        'upvotes_power': DEFAULT_VOTING_POWER
                    },
                },
                'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
            },
            'promotion_period': None, 
            'winner_payload': None
        }

    def test_should_reset_proposals_when_promotion_period_is_skipped(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_blocks(4)

        # Period index: 2. Block: 1 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 2
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == {
            'finished_at_period_index': 2, 
            'proposal_period': {
                'proposals': {
                    b'\xfa\xa8X\xa1UbF>3\xd0\xd7\xd4x\xb5J*\xe9\xcc\xfe\xa0g\x8cy#zs\xfce\x96\x90\xe6I': {
                        'payload': pack_kernel_hash(kernel_hash), 
                        'proposer': pkh(baker1), 
                        'voters': [pkh(baker2), pkh(baker1)], 
                        'upvotes_power': DEFAULT_VOTING_POWER * 2
                    },
                },
                'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
            },
            'promotion_period': {
                'payload': pack_kernel_hash(kernel_hash),
                'voters': [],
                'yay_votes_power': 0,
                'nay_votes_power': 0,
                'pass_votes_power': 0,
                'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
            }, 
            'winner_payload': None
        }

    def test_should_prolong_to_promotion_when_proposal_period_is_finished_with_a_winner(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert state['voting_context']['period_index'] == 0
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == None
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        state = governance.get_voting_state()
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD
        assert state['voting_context']['period_index'] == 1
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': kernel_hash,
            'voters': [],
            'yay_votes_power': 0,
            'nay_votes_power': 0,
            'pass_votes_power': 0,
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }
        assert state['voting_context']['last_winner_payload'] == None
        assert state['finished_voting'] == None
