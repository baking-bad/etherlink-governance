from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import NAY_VOTE, PASS_VOTE, PROMOTION_PERIOD, PROPOSAL_PERIOD, YAY_VOTE
from tests.helpers.contracts.kernel_governance import KernelGovernance
from tests.helpers.utility import pkh
from pytezos.client import PyTezosClient

class KernelGovernancePromotionPeriodTestCase(BaseTestCase):
    def prepare_promotion_period(self, custom_config=None):
        proposer = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        config = {
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 10 # 1 bakers out of 5 voted
        }
        if custom_config is not None:
            config.update(custom_config)

        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config=config)
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
        governance.using(proposer).new_proposal(pkh(proposer), kernel_hash).send()
        self.bake_block()

        self.bake_blocks(2)

        # Period index: 1. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROMOTION_PERIOD
        assert context['voting_context']['period_index'] == 1
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': kernel_hash,
            'voters': [],
            'yay_votes_power': 0,
            'nay_votes_power': 0,
            'pass_votes_power': 0,
        }
        assert context['voting_context']['last_winner_payload'] == None

        return {
            'governance': governance,
            'proposer': proposer,
            'kernel_hash': kernel_hash
        }

    def test_should_reset_to_proposal_period_if_promotion_period_is_skipped(self) -> None:
        test = self.prepare_promotion_period()
        governance: KernelGovernance = test['governance']

        # Wait to skip the whole promotion period
        self.bake_blocks(3)
        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == None

        # Wait to skip one more period
        self.bake_blocks(3)
        # Period index: 3. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 3
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == None
    
    def test_should_reset_to_proposal_period_if_promotion_quorum_is_not_reached(self) -> None:
        test = self.prepare_promotion_period({
            'promotion_quorum': 50, # 2 bakers out of 5 will vote (40%)
            'promotion_super_majority': 10, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: KernelGovernance = test['governance']
        proposer: PyTezosClient = test['proposer']
        baker1 = self.bootstrap_baker()

        # Period index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        self.bake_block()

        # Wait to skip one more period
        self.bake_blocks(2)
        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == None

    def test_should_reset_to_proposal_period_if_promotion_super_majority_is_not_reached(self) -> None:
        test = self.prepare_promotion_period({
            'promotion_quorum': 50, # 3 bakers out of 5 will vote (60%)
            'promotion_super_majority': 51, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: KernelGovernance = test['governance']
        proposer: PyTezosClient = test['proposer']
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()

        # Period index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        governance.using(baker2).vote(pkh(baker2), PASS_VOTE).send()
        self.bake_block()

        # Wait to skip one more period
        self.bake_blocks(2)
        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == None

    def test_should_reset_to_proposal_period_if_promotion_phase_has_only_pass_votes(self) -> None:
        test = self.prepare_promotion_period({
            'promotion_quorum': 50, # 3 bakers out of 5 will vote (60%)
            'promotion_super_majority': 51, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: KernelGovernance = test['governance']
        baker2 = self.bootstrap_baker()

        # Period index: 1. Block: 1 of 3
        # governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        # governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        governance.using(baker2).vote(pkh(baker2), PASS_VOTE).send()
        self.bake_block()

        # Wait to skip one more period
        self.bake_blocks(2)
        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == None

    def test_should_reset_to_proposal_period_with_a_new_winner_if_promotion_period_passed_successfully(self) -> None:
        test = self.prepare_promotion_period({
            'promotion_quorum': 50, # 3 bakers out of 5 will vote (60%)  
            'promotion_super_majority': 40, # 1 baker will vote yay, 1 baker will vote nay (50%)
        })
        governance: KernelGovernance = test['governance']
        proposer: PyTezosClient = test['proposer']
        kernel_hash = test['kernel_hash']
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()

        # Period index: 1. Block: 1 of 3
        governance.using(proposer).vote(pkh(proposer), YAY_VOTE).send()
        governance.using(baker1).vote(pkh(baker1), NAY_VOTE).send()
        governance.using(baker2).vote(pkh(baker2), PASS_VOTE).send()
        self.bake_block()

        # Wait to skip one more period
        self.bake_blocks(2)
        # Period index: 2. Block: 1 of 3
        context = governance.get_voting_context()
        assert context['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert context['voting_context']['period_index'] == 2
        assert len(context['voting_context']['proposals']) == 0
        assert context['voting_context']['promotion'] == None
        assert context['voting_context']['last_winner_payload'] == kernel_hash

        # Check that winner preserves in future periods
        self.bake_blocks(6)
        context = governance.get_voting_context()
        assert context['voting_context']['period_index'] == 4
        assert context['voting_context']['last_winner_payload'] == kernel_hash
