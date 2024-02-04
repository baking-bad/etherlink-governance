from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PROPOSAL_ALREADY_UPVOTED, UPVOTING_LIMIT_EXCEEDED, 
    SENDER_NOT_KEY_HASH_OWNER, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, pkh

class CommitteeGovernanceUpvoteProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).upvote_proposal(pkh(baker), addresses).with_amount(1).send()

    def test_should_fail_if_sender_is_not_key_hash_owner(self) -> None:
        no_baker = self.bootstrap_no_baker()
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(SENDER_NOT_KEY_HASH_OWNER):
            governance.using(no_baker).upvote_proposal(pkh(baker), addresses).send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).upvote_proposal(pkh(no_baker), addresses).send()

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
        
        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        # Period index: 0. Block: 2 of 2
        governance.using(baker).new_proposal(pkh(baker), addresses).send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        context = governance.get_voting_context()
        assert context['voting_context']['period_index'] == 1
        assert context['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).upvote_proposal(pkh(baker), addresses).send()

    def test_should_fail_if_upvoting_limit_is_exceeded(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 7
        governance = self.deploy_committee_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 7,
            'upvoting_limit': 2
        })
        
        addresses1 = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        # Period index: 0. Block: 2 of 7
        governance.using(baker1).new_proposal(pkh(baker1), addresses1).send()
        self.bake_block()
        # Period index: 0. Block: 3 of 7
        addresses2 = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        governance.using(baker1).new_proposal(pkh(baker1), addresses2).send()
        self.bake_block()
        # Period index: 0. Block: 4 of 7
        addresses3 = ['tz1Lc2qBKEWCBeDU8npG6zCeCqpmaegRi6Jg']
        governance.using(baker2).new_proposal(pkh(baker2), addresses3).send()
        self.bake_block()
        # Period index: 0. Block: 5 of 7
        governance.using(baker3).upvote_proposal(pkh(baker3), addresses1).send()
        self.bake_block()
        # Period index: 0. Block: 6 of 7
        governance.using(baker3).upvote_proposal(pkh(baker3), addresses2).send()
        self.bake_block()

        with self.raisesMichelsonError(UPVOTING_LIMIT_EXCEEDED):
            governance.using(baker3).upvote_proposal(pkh(baker3), addresses3).send()


    def test_should_fail_if_proposal_already_upvoted_by_proposer(self) -> None:
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

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(pkh(baker), one_address).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(pkh(baker), two_addresses).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(pkh(baker), two_addresses_reversed).send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker).upvote_proposal(pkh(baker), three_addresses).send()

    def test_should_fail_if_proposal_already_upvoted_by_another_baker(self) -> None:
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
        
        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(pkh(baker1), addresses).send()
        self.bake_block()

        # Period index: 0. Block: 2 of 5
        governance.using(baker2).upvote_proposal(pkh(baker2), addresses).send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_UPVOTED):
            governance.using(baker2).upvote_proposal(pkh(baker2), addresses).send()

    def test_should_upvote_proposal_with_correct_parameters(self) -> None:
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

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 0
        
        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        addresses.sort()
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(pkh(baker1), addresses).send()
        self.bake_block()

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert list(context['voting_context']['proposals'].values())[0] == {
            'payload': addresses, 
            'proposer': pkh(baker1), 
            'voters': [pkh(baker1)], 
            'upvotes_power': DEFAULT_VOTING_POWER
        }

        # Period index: 0. Block: 2 of 5
        governance.using(baker2).upvote_proposal(pkh(baker2), addresses).send()
        self.bake_block()

        expected_voters = [pkh(baker1), pkh(baker2)]
        expected_voters.sort()
        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert list(context['voting_context']['proposals'].values())[0] == {
            'payload': addresses, 
            'proposer': pkh(baker1), 
            'voters': expected_voters, 
            'upvotes_power': DEFAULT_VOTING_POWER * 2
        }