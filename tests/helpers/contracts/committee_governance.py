from pytezos.client import PyTezosClient
from tests.helpers.contracts.governance_base import GovernanceBase
from tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join
from tests.helpers.metadata import Metadata


class CommitteeGovernance(GovernanceBase):
    @classmethod
    def originate(self, client: PyTezosClient, custom_config=None) -> OperationGroup:
        """Deploys Committee Governance"""

        metadata = Metadata.make_default(
            name='Sequencer Committee Governance',
            description='The Sequencer Committee Governance contract allows bakers to make proposals and vote on sequencer committee',
        )

        storage = self.make_storage(metadata, custom_config)
        filename = join(get_build_dir(), 'committee_governance.tz')

        return originate_from_file(filename, client, storage)
    
    def new_proposal(self, sender_key_hash : str, addresses: list[str],  url : str) -> ContractCall:
        """Creates a new proposal"""

        return self.contract.new_proposal(
            {'sender_key_hash': sender_key_hash, 'addresses': addresses, 'url': url}
        )
    
    
    def upvote_proposal(self, sender_key_hash : str, addresses: list[str]) -> ContractCall:
        """Upvotes an exist proposal"""

        return self.contract.upvote_proposal(
            {'sender_key_hash': sender_key_hash, 'addresses': addresses}
        )
    
    def vote(self, sender_key_hash : str, vote : str) -> ContractCall:
        """Votes for a hash in promotion period"""

        return self.contract.vote(
            {'sender_key_hash': sender_key_hash, 'vote': vote}
        )
