from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, PROPOSAL_PERIOD, YAY_VOTE
from tests.helpers.errors import (
    INCORRECT_SEQUENCER_UPGRADE_PAYLOAD_SIZE, NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PROPOSAL_ALREADY_CREATED, PROPOSER_NOT_ALLOWED, 
    UPVOTING_LIMIT_EXCEEDED, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER, pkh

class CommitteeGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_proposal_payload_has_incorrect_size(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()

        with self.raisesMichelsonError(INCORRECT_SEQUENCER_UPGRADE_PAYLOAD_SIZE):
            governance.using(baker).new_proposal(bytes.fromhex('6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d38576439734456433979617671c7656ec7ab88b098defb751b7401b5f6d8976faaaa')).send()
        with self.raisesMichelsonError(INCORRECT_SEQUENCER_UPGRADE_PAYLOAD_SIZE):
            governance.using(baker).new_proposal(bytes.fromhex('6564706b75426b6e5732')).send()
        governance.using(baker).new_proposal(bytes.fromhex('6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d38576439734456433979617671c7656ec7ab88b098defb751b7401b5f6d8976f')).send()
        self.bake_block()

    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance()

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).new_proposal(payload).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_sequencer_governance()

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).new_proposal(payload).send()

    def test_should_not_fail_if_payload_same_as_last_winner(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20, # 1 bakers out of 5 voted
            'promotion_quorum': 20, # 1 bakers out of 5 voted
            'promotion_supermajority': 50, # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(baker).new_proposal(payload).send()
        self.bake_blocks(2)

        # Period index: 1. Block: 1 of 2
        governance.using(baker).vote(YAY_VOTE).send()
        self.bake_blocks(2)

        # Period index: 3. Block: 1 of 2
        governance.using(baker).new_proposal(payload).send()
        self.bake_block()

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

        # Period index: 0. Block: 2 of 2
        payload1 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")

        governance.using(baker).new_proposal(payload1).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        payload2 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d897ff'}")

        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).new_proposal(payload2).send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        # Period index: 0. Block: 2 of 5
        payload1 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(baker).new_proposal(payload1).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        payload2 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796186'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(baker).new_proposal(payload2).send()
        self.bake_block()

        payload3 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796196'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker).new_proposal(payload3).send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
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

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(payload).send()

    def test_should_fail_if_proposer_is_not_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        disallowed_baker = self.bootstrap_baker()
        governance = self.deploy_sequencer_governance(custom_config={
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        with self.raisesMichelsonError(PROPOSER_NOT_ALLOWED):
            governance.using(disallowed_baker).new_proposal(payload).send()

    def test_should_not_fail_if_allowed_proposers_list_is_empty(self) -> None:
        disallowed_baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'allowed_proposers': []
        })

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        governance.using(disallowed_baker).new_proposal(payload).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 2
            },
            'finished_voting': None
        }

    def test_should_not_fail_if_proposer_is_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")

        governance.using(allowed_baker).new_proposal(payload).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 2
            },
            'finished_voting': None
        }

    def test_should_not_fail_if_no_baker_is_in_the_allowed_proposers_list(self) -> None:
        no_baker = self.bootstrap_no_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_sequencer_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'allowed_proposers': [pkh(no_baker)]
        })

        payload = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")

        governance.using(no_baker).new_proposal(payload).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == payload
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == 0
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 2
            },
            'finished_voting': None
        }

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
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

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'remaining_blocks': 5
            },
            'finished_voting': None
        }
        
        payload1 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")

        # Period index: 0. Block: 2 of 5
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
                'remaining_blocks': 4
            },
            'finished_voting': None
        }

        payload2 = bytes.fromhex(f"{'6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796186'}{'71c7656ec7ab88b098defb751b7401b5f6d8976f'}")
        # Period index: 0. Block: 3 of 5
        governance.using(baker2).new_proposal(payload2).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == None
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
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