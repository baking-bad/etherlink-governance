from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import YEA_VOTE
from tests.helpers.errors import (
    LAST_WINNER_NOT_FOUND
)
from tests.helpers.utility import TEST_ADDRESSES_SET, pkh

class ProposersGovernanceCheckAddressInLastWinner(BaseTestCase):
    def test_should_fail_if_no_winner_yet(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_proposers_governance()

        with self.raisesMichelsonError(LAST_WINNER_NOT_FOUND):
            governance.using(baker).check_address_in_last_winner(TEST_ADDRESSES_SET[0])

    def test_should_check_correctly_for_originated_contract_with_winner(self) -> None:
        sender = self.bootstrap_baker()
        allowed_baker = self.bootstrap_baker()
        another_allowed_baker = self.bootstrap_baker()
        governance = self.deploy_proposers_governance(
            last_winner=[pkh(allowed_baker), pkh(another_allowed_baker)]
        )

        assert governance.using(sender).check_address_in_last_winner(pkh(allowed_baker)) == True
        assert governance.using(sender).check_address_in_last_winner(pkh(another_allowed_baker)) == True
        assert governance.using(sender).check_address_in_last_winner(pkh(sender)) == False

    def test_should_check_correctly_after_full_voting_cycle_with_new_winner(self) -> None:
        baker = self.bootstrap_baker()
        previously_allowed_baker = self.bootstrap_baker()
        new_allowed_baker = self.bootstrap_baker()
        new_another_allowed_baker = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_proposers_governance(
            custom_config={
                'started_at_level': governance_started_at_level,
                'period_length': 2,
                'proposal_quorum': 20, # 1 baker out of 5 will vote,
                'promotion_quorum': 20, # 1 bakers out of 5 will vote (20%)  
                'promotion_supermajority': 50, # 1 baker will vote yea
            },
            last_winner=[pkh(previously_allowed_baker)]
        )

        assert governance.using(baker).check_address_in_last_winner(pkh(previously_allowed_baker)) == True
        assert governance.using(baker).check_address_in_last_winner(pkh(new_allowed_baker)) == False
        assert governance.using(baker).check_address_in_last_winner(pkh(new_another_allowed_baker)) == False

        addresses = [pkh(new_allowed_baker), pkh(new_another_allowed_baker)]
        governance.using(baker).new_proposal(addresses).send()
        self.bake_blocks(2)

        assert governance.using(baker).check_address_in_last_winner(pkh(previously_allowed_baker)) == True
        assert governance.using(baker).check_address_in_last_winner(pkh(new_allowed_baker)) == False
        assert governance.using(baker).check_address_in_last_winner(pkh(new_another_allowed_baker)) == False
        
        governance.using(baker).vote(YEA_VOTE).send()
        self.bake_blocks(2)

        assert governance.using(baker).check_address_in_last_winner(pkh(previously_allowed_baker)) == False
        assert governance.using(baker).check_address_in_last_winner(pkh(new_allowed_baker)) == True
        assert governance.using(baker).check_address_in_last_winner(pkh(new_another_allowed_baker)) == True

        addresses2 = [pkh(previously_allowed_baker)]
        governance.using(baker).new_proposal(addresses2).send()
        self.bake_blocks(2)

        assert governance.using(baker).check_address_in_last_winner(pkh(previously_allowed_baker)) == False
        assert governance.using(baker).check_address_in_last_winner(pkh(new_allowed_baker)) == True
        assert governance.using(baker).check_address_in_last_winner(pkh(new_another_allowed_baker)) == True

