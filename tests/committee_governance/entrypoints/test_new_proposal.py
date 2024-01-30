from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROMOTION_PERIOD
from tests.helpers.errors import (
    NO_VOTING_POWER, NOT_PROPOSAL_PERIOD, PROPOSAL_ALREADY_CREATED, 
    PROPOSAL_LIMIT_EXCEEDED, SENDER_NOT_KEY_HASH_OWNER, XTZ_IN_TRANSACTION_DISALLOWED
)
from tests.helpers.utility import DEFAULT_VOTING_POWER, pack_kernel_hash, pkh

class CommitteeGovernanceNewProposalTestCase(BaseTestCase):
    def test_should_fail_if_xtz_in_transaction(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(XTZ_IN_TRANSACTION_DISALLOWED):
            governance.using(baker).new_proposal(pkh(baker), addresses, 'abc.com').with_amount(1).send()

    def test_should_fail_if_sender_is_not_key_hash_owner(self) -> None:
        no_baker = self.bootstrap_no_baker()
        baker = self.bootstrap_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(SENDER_NOT_KEY_HASH_OWNER):
            governance.using(no_baker).new_proposal(pkh(baker), addresses, 'abc.com').send()

    def test_should_fail_if_sender_has_no_voting_power(self) -> None:
        no_baker = self.bootstrap_no_baker()
        governance = self.deploy_committee_governance()

        addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(NO_VOTING_POWER):
            governance.using(no_baker).new_proposal(pkh(no_baker), addresses, 'abc.com').send()

    def test_should_fail_if_current_period_is_not_proposal(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_committee_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 2,
            'min_proposal_quorum': 20 # 1 bakers out of 5 voted
        })

        # Period index: 0. Block: 2 of 2
        addresses1 = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        governance.using(baker).new_proposal(pkh(baker), addresses1, 'abc.com').send()
        self.bake_block()

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        context = governance.get_voting_context()
        assert context['voting_context']['period_index'] == 1
        assert context['voting_context']['period_type'] == PROMOTION_PERIOD

        # Period index: 1. Block: 2 of 2
        addresses2 = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        with self.raisesMichelsonError(NOT_PROPOSAL_PERIOD):
            governance.using(baker).new_proposal(pkh(baker), addresses2, 'bcd.com').send()

    def test_should_fail_if_new_proposal_limit_is_exceeded(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 2
        })
        
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(pkh(baker), ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa'], 'abc.com').send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(pkh(baker), ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1'], 'bcd.com').send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_LIMIT_EXCEEDED):
            governance.using(baker).new_proposal(pkh(baker), ['tz1Lc2qBKEWCBeDU8npG6zCeCqpmaegRi6Jg'], 'cde.com').send()

    def test_should_fail_if_new_proposal_already_created(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 5
        })
        
        one_address = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        two_addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        two_addresses_reversed = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1', 'tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa']
        three_addresses = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1', 'tz1Lc2qBKEWCBeDU8npG6zCeCqpmaegRi6Jg']
        # Period index: 0. Block: 1 of 5
        governance.using(baker).new_proposal(pkh(baker), one_address, 'abc.com').send()
        self.bake_block()
        # Period index: 0. Block: 2 of 5
        governance.using(baker).new_proposal(pkh(baker), two_addresses, 'abc.com').send()
        self.bake_block()
        # Period index: 0. Block: 3 of 5
        governance.using(baker).new_proposal(pkh(baker), three_addresses, 'abc.com').send()
        self.bake_block()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), one_address, 'abc.com').send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), two_addresses, 'abc.com').send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), two_addresses_reversed, 'abc.com').send()

        with self.raisesMichelsonError(PROPOSAL_ALREADY_CREATED):
            governance.using(baker).new_proposal(pkh(baker), three_addresses, 'abc.com').send()

    def test_should_create_new_proposal_with_correct_parameters(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_block = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 5
        governance = self.deploy_committee_governance(custom_config={
            'started_at_block': governance_started_at_block,
            'period_length': 5,
            'proposals_limit_per_account': 2
        })

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 0
        
        addresses1 = ['tz1RoqRN77gGpeV96vEXzt62Sns2LViZiUCa', 'tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        addresses1.sort()
        # Period index: 0. Block: 1 of 5
        governance.using(baker1).new_proposal(pkh(baker1), addresses1, 'abc.com').send()
        self.bake_block()

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 1
        assert list(context['voting_context']['proposals'].values())[0] == {
            'payload': addresses1, 
            'url': 'abc.com', 
            'proposer': pkh(baker1), 
            'voters': [pkh(baker1)], 
            'up_votes_power': DEFAULT_VOTING_POWER
        }

        addresses2 = ['tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1']
        # Period index: 0. Block: 2 of 5
        governance.using(baker2).new_proposal(pkh(baker2), addresses2, 'bcd.com').send()
        self.bake_block()

        context = governance.get_voting_context()
        assert len(context['voting_context']['proposals']) == 2
        assert list(context['voting_context']['proposals'].values())[0] == {
            'payload': addresses1, 
            'url': 'abc.com', 
            'proposer': pkh(baker1), 
            'voters': [pkh(baker1)], 
            'up_votes_power': DEFAULT_VOTING_POWER
        }
        assert list(context['voting_context']['proposals'].values())[1] == {
            'payload': addresses2, 
            'url': 'bcd.com', 
            'proposer': pkh(baker2), 
            'voters': [pkh(baker2)], 
            'up_votes_power': DEFAULT_VOTING_POWER
        }