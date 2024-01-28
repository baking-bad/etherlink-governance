from tests.base import BaseTestCase
from tests.helpers.contracts.governance import PROPOSAL_PERIOD, PROMOTION_PERIOD
from tests.helpers.utility import pkh

class GovernanceProposalPeriodTestCase(BaseTestCase):
    def test_should_reset_proposals_when_no_proposals(self) -> None:
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 3
        })
        assert self.get_current_level() == governance_started_at_block

        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()
        # Period index: 0. Block: 2 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None
        
        self.bake_block()
        # Period index: 0. Block: 3 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()
        # Period index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()
        # Period index: 1. Block: 2 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_blocks(10)
        # Period index: 1. Block: 2 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 4
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_proposals_when_period_is_finished_with_no_votes_except_proposer(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 2,
            'min_proposal_quorum': 40 # 1 baker out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_block

        # Period index: 0. Block: 2 of 2
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_proposals_when_period_is_finished_with_not_enough_votes(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 3,
            'min_proposal_quorum': 60 # 2 bakers out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_block

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_proposals_when_period_is_finished_with_2_winners(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 3,
            'min_proposal_quorum': 20 # 1 bakers out of 5 will vote for each proposal
        })
        assert self.get_current_level() == governance_started_at_block

        # Period index: 0. Block: 2 of 3
        kernel_hash1 = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash1, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        # Period index: 0. Block: 3 of 3
        kernel_hash2 = bytes.fromhex('0202020202020202020202020202020202020202')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash2, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 2
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_proposals_when_promotion_period_is_skipped(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 3,
            'min_proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_block

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_blocks(4)

        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_prolong_to_promotion_when_proposal_period_is_finished_with_a_winner(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 3,
            'min_proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_block

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash, 'abc.com').send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(pkh(baker2), kernel_hash).send()
        self.bake_block()
        
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 0
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROMOTION_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_hash': kernel_hash,
            'voters': [],
            'yay_vote_power': 0,
            'nay_vote_power': 0,
            'pass_vote_power': 0,
        }
        assert context['voting_context']['last_winner_hash'] == None