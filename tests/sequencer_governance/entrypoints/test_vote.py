from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import NAY_VOTE, PASS_VOTE, PROMOTION_PERIOD, PROPOSAL_PERIOD, YAY_VOTE
from tests.helpers.errors import (
    INCORRECT_VOTE_VALUE, NO_VOTING_POWER, NOT_PROMOTION_PERIOD, PROMOTION_ALREADY_VOTED, 
    XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER, pkh

class CommitteeGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()

        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).vote(YAY_VOTE).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_sequencer_governance()

        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).vote(YAY_VOTE).send()

    def test_should_fail_if_current_period_is_not_promotion(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()

        with self.raisesMichelsonError(NOT_PROMOTION_PERIOD):
            governance.using(baker).vote(YAY_VOTE).send()

    def test_should_fail_if_vote_parameter_is_incorrect(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 3
        governance.using(baker1).new_proposal(payload).send()
        self.bake_block()
        
        # Period index: 0. Block: 3 of 3
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_block()

        # Period index: 1. Block: 2 of 3
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote("yep").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote("no").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote("pas").send()
        with self.raisesMichelsonError(INCORRECT_VOTE_VALUE):
            governance.using(baker1).vote("NAY").send()

        governance.using(baker1).vote("yay").send()
        governance.using(baker2).vote("nay").send()
        governance.using(baker3).vote("pass").send()
        self.bake_block()

    def test_should_fail_if_proposal_already_voted(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 3
        governance.using(baker).new_proposal(payload).send()
        self.bake_block()
        
        # Period index: 0. Block: 3 of 3
        self.bake_block()
        # Period index: 1. Block: 1 of 3
        self.bake_block()

        # Period index: 1. Block: 2 of 3
        governance.using(baker).vote(YAY_VOTE).send()
        self.bake_block()

        with self.raisesMichelsonError(PROMOTION_ALREADY_VOTED):
            governance.using(baker).vote(YAY_VOTE).send()

    def test_should_vote_on_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        baker4 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 5
            },
            'finished_voting': None
        }
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 5
        governance.using(baker1).new_proposal(payload).send()
        self.bake_block()
        # Period index: 1. Block: 1 of 5
        self.bake_blocks(4)

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'remaining_blocks': 5
            },
            'finished_voting': None
        }

        # Period index: 1. Block: 2 of 5
        governance.using(baker1).vote(YAY_VOTE).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROMOTION_PERIOD
        assert storage['voting_context']['period_index'] == 1
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period']['yay_voting_power'] == DEFAULT_VOTING_POWER 
        assert storage['voting_context']['promotion_period']['nay_voting_power'] == 0
        assert storage['voting_context']['promotion_period']['pass_voting_power'] == 0 
        assert storage['voting_context']['promotion_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER 
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'remaining_blocks': 4
            },
            'finished_voting': None
        }


        # Period index: 1. Block: 3 of 5
        governance.using(baker2).vote(NAY_VOTE).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROMOTION_PERIOD
        assert storage['voting_context']['period_index'] == 1
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period']['yay_voting_power'] == DEFAULT_VOTING_POWER 
        assert storage['voting_context']['promotion_period']['nay_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['promotion_period']['pass_voting_power'] == 0 
        assert storage['voting_context']['promotion_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER 
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'remaining_blocks': 3
            },
            'finished_voting': None
        }

        # Period index: 1. Block: 4 of 5
        governance.using(baker3).vote(PASS_VOTE).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROMOTION_PERIOD
        assert storage['voting_context']['period_index'] == 1
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period']['yay_voting_power'] == DEFAULT_VOTING_POWER 
        assert storage['voting_context']['promotion_period']['nay_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['promotion_period']['pass_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['promotion_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER 
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'remaining_blocks': 2
            },
            'finished_voting': None
        }

        # Period index: 1. Block: 5 of 5
        governance.using(baker4).vote(YAY_VOTE).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROMOTION_PERIOD
        assert storage['voting_context']['period_index'] == 1
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period']['yay_voting_power'] == DEFAULT_VOTING_POWER  * 2
        assert storage['voting_context']['promotion_period']['nay_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['promotion_period']['pass_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['promotion_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER 
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'remaining_blocks': 1
            },
            'finished_voting': None
        }