from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import NAY_VOTE, PASS_VOTE, YAY_VOTE
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROMOTION_PERIOD, PROMOTION_ALREADY_VOTED, 
    SENDER_NOT_KEY_HASH_OWNER, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, pack_kernel_hash, pkh

class KernelGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).vote(pkh(baker), YAY_VOTE).with_amount(1).send()

    def test_should_fail_if_sender_is_not_key_hash_owner(self) -> None:
        no_baker = self.bootstrap_no_baker()
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(SENDER_NOT_KEY_HASH_OWNER):
            governance.using(no_baker).vote(pkh(baker), YAY_VOTE).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).vote(pkh(no_baker), YAY_VOTE).send()

    def test_should_fail_if_current_period_is_not_promotion(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_kernel_governance()

        with self.raisesMichelsonError(NOT_PROMOTION_PERIOD):
            governance.using(baker).vote(pkh(baker), YAY_VOTE).send()

    def test_should_fail_if_proposal_already_voted(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'min_proposal_quorum': 20 # 1 baker out of 5 will vote
        })
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 2 of 3
        governance.using(baker).new_proposal(pkh(baker), kernel_hash).send()
        self.bake_block()
        
        # Period index: 0. Block: 3 of 3
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_block()

        # Period index: 1. Block: 2 of 3
        governance.using(baker).vote(pkh(baker), YAY_VOTE).send()
        self.bake_block()

        with self.raisesMichelsonError(PROMOTION_ALREADY_VOTED):
            governance.using(baker).vote(pkh(baker), YAY_VOTE).send()

    def test_should_vote_on_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        baker4 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2,
            'min_proposal_quorum': 20 # 1 baker out of 5 will vote
        })

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 0
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 2 of 5
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_blocks(3)

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': pack_kernel_hash(kernel_hash),
            'voters': [],
            'yay_votes_power': 0,
            'nay_votes_power': 0,
            'pass_votes_power': 0,
        }

        # Period index: 1. Block: 2 of 5
        governance.using(baker1).vote(pkh(baker1), YAY_VOTE).send()
        self.bake_block()

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': pack_kernel_hash(kernel_hash),
            'voters': [pkh(baker1)],
            'yay_votes_power': DEFAULT_VOTING_POWER,
            'nay_votes_power': 0,
            'pass_votes_power': 0,
        }

        # Period index: 1. Block: 3 of 5
        governance.using(baker2).vote(pkh(baker2), NAY_VOTE).send()
        self.bake_block()

        expected_voters = [pkh(baker1), pkh(baker2)]
        expected_voters.sort()
        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': pack_kernel_hash(kernel_hash),
            'voters': expected_voters,
            'yay_votes_power': DEFAULT_VOTING_POWER,
            'nay_votes_power': DEFAULT_VOTING_POWER,
            'pass_votes_power': 0,
        }

        # Period index: 1. Block: 4 of 5
        governance.using(baker3).vote(pkh(baker3), PASS_VOTE).send()
        self.bake_block()

        expected_voters = [pkh(baker1), pkh(baker2), pkh(baker3)]
        expected_voters.sort()
        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': pack_kernel_hash(kernel_hash),
            'voters': expected_voters,
            'yay_votes_power': DEFAULT_VOTING_POWER,
            'nay_votes_power': DEFAULT_VOTING_POWER,
            'pass_votes_power': DEFAULT_VOTING_POWER,
        }

        # Period index: 1. Block: 5 of 5
        governance.using(baker4).vote(pkh(baker4), YAY_VOTE).send()
        self.bake_block()

        expected_voters = [pkh(baker1), pkh(baker2), pkh(baker3), pkh(baker4)]
        expected_voters.sort()
        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert context['voting_context']['promotion'] == {
            'proposal_payload': pack_kernel_hash(kernel_hash),
            'voters': expected_voters,
            'yay_votes_power': DEFAULT_VOTING_POWER * 2,
            'nay_votes_power': DEFAULT_VOTING_POWER,
            'pass_votes_power': DEFAULT_VOTING_POWER,
        }