from tests.helpers.contracts.contract import ContractHelper
from typing import (
    Any,
)

PROPOSAL_PERIOD = 'proposal'
PROMOTION_PERIOD = 'promotion'

YAY_VOTE = 'yay'
NAY_VOTE = 'nay'
PASS_VOTE = 'pass'

class GovernanceBase(ContractHelper):
    @staticmethod
    def make_storage(metadata: dict[str, Any], custom_config=None) -> dict[str, Any]:
        config = {
            'started_at_block': 0,
            'period_length': 10,
            'proposals_limit_per_account': 20,
            'min_proposal_quorum': 80,
            'quorum': 80,
            'super_majority': 80,
        }
        if custom_config is not None:
            config.update(custom_config)

        return {
            'config' : config,
            'voting_context' : {
                'period_index' : 0,
                'period_type' : PROPOSAL_PERIOD,
                'proposals' : {},
                'promotion' : None,  
                'last_winner_payload' : None,
            },
            'metadata': metadata
        }

    def get_voting_context(self):
        return self.contract.get_voting_context().run_view()