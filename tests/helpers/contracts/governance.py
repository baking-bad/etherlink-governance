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

class Governance(ContractHelper):
    @staticmethod
    def make_storage() -> dict[str, Any]:
        metadata = Metadata.make_default(
            name='Governance',
            description='The Governance contract allows bakers to make proposals and vote on kernel upgrade',
        )
        return {
            'config' : {
                'rollup_address' : DEFAULT_ADDRESS,
                'phase_length' : 10,
                'proposals_limit_per_account' : 20,
                'min_proposal_quorum' : 80,
                'quorum' : 80,
                'super_majority' : 80,
            },
            'voting_context' : {
                'phase_index' : 0,
                'phase_type' : 0,
                'proposals' : {},
                'promotion' : None,  
                'last_promotion_winner_hash' : None,
            },
            'metadata': metadata
        }

    @classmethod
    def originate(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Governance"""

        storage = cls.make_storage()
        filename = join(get_build_dir(), 'governance.tz')

        return originate_from_file(filename, client, storage)
    
    def new_proposal(self, key_hash : str, hash : bytes, url : str) -> ContractCall:
        """Creates a new proposal"""

        return self.contract.new_proposal(
            {'key_hash': key_hash, 'hash': hash, 'url': url}
        )
    