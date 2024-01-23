from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
    DEFAULT_ADDRESS,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join
from tests.helpers.metadata import Metadata
from typing import (
    Any,
)


PROPOSAL_PHASE = 'proposal'
PROMOTION_PHASE = 'promotion'

YAY_VOTE = 'yay'
NAY_VOTE = 'nay'
PASS_VOTE = 'pass'

class Governance(ContractHelper):
    @staticmethod
    def make_storage(custom_config=None) -> dict[str, Any]:
        metadata = Metadata.make_default(
            name='Governance',
            description='The Governance contract allows bakers to make proposals and vote on kernel upgrade',
        )
        config = {
            'started_at_block': 0,
            'phase_length': 10,
            'rollup_address': DEFAULT_ADDRESS,
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
                'phase_index' : 0,
                'phase_type' : PROPOSAL_PHASE,
                'proposals' : {},
                'promotion' : None,  
                'last_winner_hash' : None,
            },
            'metadata': metadata
        }

    @classmethod
    def originate(cls, client: PyTezosClient, custom_config=None) -> OperationGroup:
        """Deploys Governance"""

        storage = cls.make_storage(custom_config=custom_config)
        filename = join(get_build_dir(), 'governance.tz')

        return originate_from_file(filename, client, storage)
    
    def new_proposal(self, sender_key_hash : str, hash : bytes, url : str) -> ContractCall:
        """Creates a new proposal"""

        return self.contract.new_proposal(
            {'sender_key_hash': sender_key_hash, 'hash': hash, 'url': url}
        )
    
    
    def upvote_proposal(self, sender_key_hash : str, hash : bytes) -> ContractCall:
        """Upvotes an exist proposal"""

        return self.contract.upvote_proposal(
            {'sender_key_hash': sender_key_hash, 'hash': hash}
        )
    
    def vote(self, sender_key_hash : str, vote : str) -> ContractCall:
        """Votes for a hash in promotion phase"""

        return self.contract.vote(
            {'sender_key_hash': sender_key_hash, 'vote': vote}
        )
    
    def get_voting_context(self):
        return self.contract.get_voting_context().run_view()