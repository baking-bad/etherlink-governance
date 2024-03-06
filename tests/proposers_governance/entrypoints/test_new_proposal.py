from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD, PROPOSAL_PERIOD, YEA_VOTE
from tests.helpers.errors import (
    INCORRECT_ADDRESSES_SIZE, NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, 
    PROPOSAL_ALREADY_CREATED, PROPOSER_NOT_IN_COMMITTEE, UPVOTING_LIMIT_EXCEEDED, 
    TEZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER, TEST_ADDRESSES_SET, pkh

class ProposersGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_addresses_set_has_incorrect_size(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_proposers_governance()

        assert len(TEST_ADDRESSES_SET) > 20

        with self.raisesMichelsonError(INCORRECT_ADDRESSES_SIZE):
            governance.using(baker).new_proposal(TEST_ADDRESSES_SET).send()
        governance.using(baker).new_proposal(TEST_ADDRESSES_SET[0:20]).send()
        self.bake_block()

    def test_should_fail_if_tez_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_proposers_governance()

        addresses = TEST_ADDRESSES_SET[0:3]
        with self.raisesMichelsonError(TEZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).new_proposal(addresses).with_amount(1).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_proposers_governance()

        addresses = TEST_ADDRESSES_SET[0:2]
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).new_proposal(addresses).send()

    def test_should_not_fail_if_payload_same_as_last_winner(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20, # 1 bakers out of 5 voted
            'promotion_quorum': 20, # 1 bakers out of 5 voted
            'promotion_supermajority': 50, # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        addresses = TEST_ADDRESSES_SET[0:4]
        governance.using(baker).new_proposal(addresses).send()
        self.bake_blocks(2)

        # Period index: 1. Block: 1 of 2
        governance.using(baker).vote(YEA_VOTE).send()
        self.bake_blocks(2)

        # Period index: 3. Block: 1 of 2
        governance.using(baker).new_proposal(addresses).send()
        self.bake_block()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20 # 1 bakers out of 5 voted
        })
        
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(TEST_ADDRESSES_SET[0:2]).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        state = governance.get_voting_state()
        assert state['period_index'] == 1
        assert state['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        kernel_root_hash = TEST_ADDRESSES_SET[1:3]
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).new_proposal(kernel_root_hash).send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(TEST_ADDRESSES_SET[0:2]).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(TEST_ADDRESSES_SET[1:3]).send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker).new_proposal(TEST_ADDRESSES_SET[4:5]).send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })
        
        addresses = TEST_ADDRESSES_SET[2:5]
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(addresses).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(addresses).send()

    def test_should_fail_if_proposer_is_not_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        disallowed_baker = self.bootstrap_baker()
        proposers_governance = self.deploy_proposers_governance(
            last_winner=[pkh(allowed_baker), pkh(another_allowed_baker)]
        )
        governance = self.deploy_proposers_governance(custom_config={
            'proposers_governance_contract': proposers_governance.address
        })

        addresses = TEST_ADDRESSES_SET[2:5]
        with self.raisesMichelsonError(PROPOSER_NOT_IN_COMMITTEE):
            governance.using(disallowed_baker).new_proposal(addresses).send()

    def test_should_not_fail_if_proposers_governance_contract_address_is_none(self) -> None:
        disallowed_baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposers_governance_contract': None
        })

        addresses = TEST_ADDRESSES_SET[2:5]
        governance.using(disallowed_baker).new_proposal(addresses).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == addresses
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 2,
            'finished_voting': None
        }

    def test_should_not_fail_if_proposer_is_in_the_allowed_proposers_list(self) -> None:
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        proposers_governance = self.deploy_proposers_governance(
            last_winner=[pkh(allowed_baker), pkh(another_allowed_baker)]
        )
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposers_governance_contract': proposers_governance.address
        })

        addresses = TEST_ADDRESSES_SET[2:5]
        governance.using(allowed_baker).new_proposal(addresses).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == addresses
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 2,
            'finished_voting': None
        }

    def test_should_not_fail_if_no_baker_is_in_the_allowed_proposers_list(self) -> None:
        no_baker = self.bootstrap_no_baker()
        proposers_governance = self.deploy_proposers_governance(
            last_winner=[pkh(no_baker)]
        )
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposers_governance_contract': proposers_governance.address
        })

        addresses = TEST_ADDRESSES_SET[3:7]
        governance.using(no_baker).new_proposal(addresses).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == addresses
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == 0
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 2,
            'finished_voting': None
        }

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_proposers_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 5,
            'upvoting_limit': 2
        })

        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 5,
            'finished_voting': None
        }
        
        addresses1 = TEST_ADDRESSES_SET[3:4]
        # Period index: 0. Block: 2 of 5
        governance.using(baker1).new_proposal(addresses1).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == addresses1
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 4,
            'finished_voting': None
        }

        addresses2 = TEST_ADDRESSES_SET[0:4]
        # Period index: 0. Block: 3 of 5
        governance.using(baker2).new_proposal(addresses2).send()
        self.bake_block()

        storage = governance.contract.storage()
        assert storage['voting_context']['period_type'] == PROPOSAL_PERIOD
        assert storage['voting_context']['period_index'] == 0
        assert storage['voting_context']['proposal_period']['winner_candidate'] == None
        assert storage['voting_context']['proposal_period']['max_upvotes_voting_power'] == DEFAULT_VOTING_POWER
        assert storage['voting_context']['proposal_period']['total_voting_power'] == DEFAULT_TOTAL_VOTING_POWER
        assert storage['voting_context']['promotion_period'] == None
        assert governance.get_voting_state() == {
            'period_type': PROPOSAL_PERIOD,
            'period_index': 0,
            'remaining_blocks': 3,
            'finished_voting': None
        }