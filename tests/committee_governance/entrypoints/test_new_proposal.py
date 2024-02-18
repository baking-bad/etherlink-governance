from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, YAY_VOTE
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PAYLOAD_SAME_AS_LAST_WINNER, PROPOSAL_ALREADY_CREATED, PROPOSER_NOT_ALLOWED, 
    UPVOTING_LIMIT_EXCEEDED, SENDER_NOT_KEY_HASH_OWNER, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, pack_kernel_hash, pkh

class CommitteeGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).new_proposal(pkh(baker), addresses).with_amount(1).send()

    def test_should_fail_if_sender_is_not_key_hash_owner(self) -> None:
        no_baker = self.bootstrap_no_baker()
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(SENDER_NOT_KEY_HASH_OWNER):
            governance.using(no_baker).new_proposal(pkh(baker), addresses).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).new_proposal(pkh(no_baker), addresses).send()

    def test_should_fail_payload_same_as_last_winner(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20, # 1 bakers out of 5 voted
            'promotion_quorum': 20, # 1 bakers out of 5 voted
            'promotion_supermajority': 50, # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        governance.using(baker).new_proposal(pkh(baker), addresses).send()
        self.bake_blocks(2)

        # Period index: 1. Block: 1 of 2
        governance.using(baker).vote(pkh(baker), YAY_VOTE).send()
        self.bake_blocks(2)

        # Period index: 3. Block: 1 of 2
        with self.raisesMichelsonError(PAYLOAD_SAME_AS_LAST_WINNER):
            governance.using(baker).new_proposal(pkh(baker), addresses).send()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20 # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        addresses1 = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        governance.using(baker).new_proposal(pkh(baker), addresses1).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['voting_context']['period_index'] == 1
        assert state['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        addresses2 = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).new_proposal(pkh(baker), addresses2).send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(pkh(baker), ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(pkh(baker), ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']).send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker).new_proposal(pkh(baker), ['tz1Lc2qBKEWCBeDU8npG6zCeCqpmaegRi6Jg']).send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 5
        })
        
        one_address = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        two_addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        two_addresses_reversed = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1', 'tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        three_addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1', 'tz1Lc2qBKEWCBeDU8npG6zCeCqpmaegRi6Jg']
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(pkh(baker), one_address).send()
        self.bake_block()
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(pkh(baker), two_addresses).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(pkh(baker), three_addresses).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), one_address).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), two_addresses).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), two_addresses_reversed).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), three_addresses).send()
            
    def test_should_fail_if_proposer_is_not_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        disallowed_baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance(custom_config={
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(PROPOSER_NOT_ALLOWED):
            governance.using(disallowed_baker).new_proposal(pkh(disallowed_baker), addresses).send()

    def test_should_not_fail_if_allowed_proposers_list_is_empty(self) -> None:
        disallowed_baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance(custom_config={
            'allowed_proposers': []
        })

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        governance.using(disallowed_baker).new_proposal(pkh(disallowed_baker), addresses).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_not_fail_if_proposer_is_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance(custom_config={
            'allowed_proposers': [pkh(allowed_baker), pkh(another_allowed_baker)]
        })

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        governance.using(allowed_baker).new_proposal(pkh(allowed_baker), addresses).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_not_fail_if_no_baker_is_in_the_allowed_proposers_list(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_committee_governance(custom_config={
            'allowed_proposers': [pkh(no_baker)]
        })

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        governance.using(no_baker).new_proposal(pkh(no_baker), addresses).send()
        self.bake_block()
        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 0
        
        addresses1 = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        addresses1.sort()
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(pkh(baker1), addresses1).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 1
        assert list(state['voting_context']['proposal_period']['proposals'].values())[0] == {
            'payload': addresses1, 
            'proposer': pkh(baker1), 
            'votes': {
                pkh(baker1): DEFAULT_VOTING_POWER
            },
        }

        addresses2 = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        # Period index: 0. Block: 2 of 5
        governance.using(baker2).new_proposal(pkh(baker2), addresses2).send()
        self.bake_block()

        state = governance.get_voting_state()
        assert len(state['voting_context']['proposal_period']['proposals']) == 2
        assert list(state['voting_context']['proposal_period']['proposals'].values())[0] == {
            'payload': addresses1, 
            'proposer': pkh(baker1), 
            'votes': {
                pkh(baker1): DEFAULT_VOTING_POWER
            },
        }
        assert list(state['voting_context']['proposal_period']['proposals'].values())[1] == {
            'payload': addresses2, 
            'proposer': pkh(baker2), 
            'votes': {
                pkh(baker2): DEFAULT_VOTING_POWER
            },
        }