from tests.base import BaseTestCase
from tests.helpers.contracts.governance import NAY_VOTE, PASS_VOTE, PROMOTION_PHASE, PROPOSAL_PHASE, YAY_VOTE, Governance
from tests.helpers.utility import pkh
from pytezos.client import PyTezosClient

class GovernancePromotionPhaseTestCase(BaseTestCase):
    def prepare_promotion_phase(self, custom_config=None):
        proposer = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        config = {
            'started_at_block': governance_started_at_block,
            'phase_length': 3,
            'min_proposal_quorum': 10 # 1 bakers out of 5 voted
        }
        if custom_config is not None:
            config.update(custom_config)

        # Phase index: 0. Block: 1 of 3
        governance = self.deploy_governance(custom_config=config)
        assert self.get_current_level() == governance_started_at_block

        # Phase index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(proposer).new_proposal(pkh(proposer), kernel_hash, 'abc.com').send()
        self.bake_block()

        self.bake_blocks(2)

        # Phase index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROMOTION_PHASE
        assert context['voting_context']['phase_index'] == 1
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_hash': kernel_hash,
            'voters': [],
            'yay_vote_power': 0,
            'nay_vote_power': 0,
            'pass_vote_power': 0,
        }
        assert context['voting_context']['last_winner_hash'] == None

        return {
            'governance': governance,
            'proposer': proposer,
            'kernel_hash': kernel_hash
        }

    def test_should_reset_to_proposal_phase_if_promotion_phase_is_skipped(self) -> None:
        test = self.prepare_promotion_phase()
        governance: Governance = test['governance']

        # Wait to skip the whole promotion phase
        self.bake_blocks(3)
        # Phase index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROPOSAL_PHASE
        assert context['voting_context']['phase_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

        # Wait to skip one more phase
        self.bake_blocks(3)
        # Phase index: 3. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROPOSAL_PHASE
        assert context['voting_context']['phase_index'] == 3
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None
    
    def test_should_reset_to_proposal_phase_if_quorum_is_not_reached(self) -> None:
        test = self.prepare_promotion_phase({
            'quorum': 50, # 2 bakers out of 5 will vote (40%)
            'super_majority': 10, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: Governance = test['governance']
        proposer: PyTezosClient = test['proposer']
        baker1 = self.bootstrap_baker()

        # Phase index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        self.bake_block()

        print('voting_context', governance.get_voting_context())

        # Wait to skip one more phase
        self.bake_blocks(2)
        # Phase index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROPOSAL_PHASE
        assert context['voting_context']['phase_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_to_proposal_phase_if_super_majority_is_not_reached(self) -> None:
        test = self.prepare_promotion_phase({
            'quorum': 50, # 3 bakers out of 5 will vote (60%)
            'super_majority': 51, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: Governance = test['governance']
        proposer: PyTezosClient = test['proposer']
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()

        # Phase index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        governance.using(baker2).vote(pkh(baker2), PASS_VOTE).send()
        self.bake_block()

        print('voting_context', governance.get_voting_context())

        # Wait to skip one more phase
        self.bake_blocks(2)
        # Phase index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROPOSAL_PHASE
        assert context['voting_context']['phase_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == None

    def test_should_reset_to_proposal_phase_with_a_new_winner_if_promotion_phase_passed_successfully(self) -> None:
        test = self.prepare_promotion_phase({
            'quorum': 50, # 3 bakers out of 5 will vote (60%)  
            'super_majority': 40, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: Governance = test['governance']
        proposer: PyTezosClient = test['proposer']
        kernel_hash = test['kernel_hash']
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()

        # Phase index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        governance.using(baker2).vote(pkh(baker2), PASS_VOTE).send()
        self.bake_block()

        print('voting_context', governance.get_voting_context())

        # Wait to skip one more phase
        self.bake_blocks(2)
        # Phase index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['phase_type'] == PROPOSAL_PHASE
        assert context['voting_context']['phase_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_hash'] == kernel_hash

        # Check that winner preserves in future phases
        self.bake_blocks(6)
        context = governance.get_voting_context()
        assert context['voting_context']['phase_index'] == 4
        assert context['voting_context']['last_winner_hash'] == kernel_hash
