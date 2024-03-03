from tests.helpers.contracts.contract import ContractHelper
from typing import (
    Any,
)

PROPOSAL_PERIOD = 'proposal'
PROMOTION_PERIOD = 'promotion'

YEA_VOTE = 'yea'
NAY_VOTE = 'nay'
PASS_VOTE = 'pass'

class GovernanceBase(ContractHelper):
    @staticmethod
    def make_storage(metadata: dict[str, Any], is_trigger_enabled: bool=True, custom_config=None, last_winner=None) -> dict[str, Any]:
        config = {
            'started_at_level': 0,
            'period_length': 10,
            'upvoting_limit': 20,
            'proposers_governance_contract': None,
            'scale': 100,
            'proposal_quorum': 80,
            'promotion_quorum': 80,
            'promotion_supermajority': 80,
        }
        if is_trigger_enabled:
            config['adoption_period_sec'] = 60

        if custom_config is not None:
            config.update(custom_config)

        return {
            'config': config,
            'voting_context': None,
            'last_winner': last_winner,
            'metadata': {}
            # 'metadata': metadata
        }
    
    def get_voting_state(self):
        return self.contract.get_voting_state().run_view()