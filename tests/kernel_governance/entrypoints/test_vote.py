from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import NAY_VOTE, PASS_VOTE, YAY_VOTE
from tests.helpers.errors import (
    INCORRECT_VOTE_VALUE, NO_VOTING_POWER, NOT_PROMOTION_PERIOD, PROMOTION_ALREADY_VOTED, 
    SENDER_NOT_KEY_HASH_OWNER, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, DEFAULT_TOTAL_VOTING_POWER, pack_kernel_hash, pkh

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


    def test_should_fail_if_vote_parameter_is_incorrect(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 2 of 3
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        
        # Period index: 0. Block: 3 of 3
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_block()

        # Period index: 1. Block: 2 of 3
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote(pkh(baker1), "yep").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote(pkh(baker1), "no").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote(pkh(baker1), "pas").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote(pkh(baker1), "NAY").send()

        governance.using(baker1).vote(pkh(baker1), "yay").send()
        governance.using(baker2).vote(pkh(baker2), "nay").send()
        governance.using(baker3).vote(pkh(baker3), "pass").send()
        self.bake_block()

    def test_should_fail_if_proposal_already_voted(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
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
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        
        kernel_hash = '0101010101010101010101010101010101010101'
        # Period index: 0. Block: 2 of 5
        governance.using(baker1).new_proposal(pkh(baker1), kernel_hash).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_blocks(3)

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': pack_kernel_hash(kernel_hash),
            'votes': {},
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }

        # Period index: 1. Block: 2 of 5
        governance.using(baker1).vote(pkh(baker1), YAY_VOTE).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': pack_kernel_hash(kernel_hash),
            'votes': {
                pkh(baker1): {
                    'vote': YAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
            },
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }

        # Period index: 1. Block: 3 of 5
        governance.using(baker2).vote(pkh(baker2), NAY_VOTE).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': pack_kernel_hash(kernel_hash),
            'votes': {
                pkh(baker1): {
                    'vote': YAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker2): {
                    'vote': NAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
            },
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }

        # Period index: 1. Block: 4 of 5
        governance.using(baker3).vote(pkh(baker3), PASS_VOTE).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': pack_kernel_hash(kernel_hash),
            'votes': {
                pkh(baker1): {
                    'vote': YAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker2): {
                    'vote': NAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker3): {
                    'vote': PASS_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
            },
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }

        # Period index: 1. Block: 5 of 5
        governance.using(baker4).vote(pkh(baker4), YAY_VOTE).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert state['voting_context']['promotion_period'] == {
            'payload': pack_kernel_hash(kernel_hash),
            'votes': {
                pkh(baker1): {
                    'vote': YAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker2): {
                    'vote': NAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker3): {
                    'vote': PASS_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
                pkh(baker4): {
                    'vote': YAY_VOTE,
                    'voting_power' : DEFAULT_VOTING_POWER
                },
            },
            'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
        }