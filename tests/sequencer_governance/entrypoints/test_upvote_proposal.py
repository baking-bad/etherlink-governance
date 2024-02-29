from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, PROPOSAL_PERIOD
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PROPOSAL_ALREADY_UPVOTED, UPVOTING_LIMIT_EXCEEDED, 
    XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER

class CommitteeGovernanceUpvoteProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).upvote_proposal(payload).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_sequencer_governance()

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).upvote_proposal(payload).send()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20 # 1 bakers out of 5 voted
        })
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(payload).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).upvote_proposal(payload).send()

    def test_should_fail_if_upvoting_limit_is_exceeded(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 7
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 7,
            'upvoting_limit': 2
        })
        
        payload1 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 7
        governance.using(baker1).new_proposal(payload1).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 7
        payload2 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796186'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(baker1).new_proposal(payload2).send()
        self.bake_block()
        # Period index: 0. Block: 4 of 7
        payload3 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796196'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(baker2).new_proposal(payload3).send()
        self.bake_block()
        # Period index: 0. Block: 5 of 7
        governance.using(baker3).upvote_proposal(payload1).send()
        self.bake_block()
        # Period index: 0. Block: 6 of 7
        governance.using(baker3).upvote_proposal(payload2).send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker3).upvote_proposal(payload3).send()


    def test_should_fail_if_proposal_already_upvoted_by_proposer(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 5
        })
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(payload).send()
        self.bake_block()
        self.bake_block()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(payload).send()

    def test_should_fail_if_proposal_already_upvoted_by_another_baker(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(payload).send()
        self.bake_block()

        # Period index: 0. Block: 2 of 5
        governance.using(baker2).upvote_proposal(payload).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker2).upvote_proposal(payload).send()

    def test_should_upvote_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 6,
            'upvoting_limit': 2
        })

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 6
            },
            'finished_voting': None
        }
        
        payload1 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 2 of 6
        governance.using(baker1).new_proposal(payload1).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload1
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 5
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 3 of 6
        governance.using(baker2).upvote_proposal(payload1).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload1
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER * 2
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 4
            },
            'finished_voting': None
        }

        payload2 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796196'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 4 of 6
        governance.using(baker1).new_proposal(payload2).send()
        self.bake_block()
        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload1
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER * 2
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 3
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 5 of 6
        governance.using(baker2).upvote_proposal(payload2).send()
        self.bake_block()
        # Period index: 0. Block: 6 of 6
        governance.using(baker3).upvote_proposal(payload2).send()
        self.bake_block()
        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload2
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER * 3
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 1
            },
            'finished_voting': None
        }