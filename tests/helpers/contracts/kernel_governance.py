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


class KernelGovernance(GovernanceBase):
    @classmethod
    def originate(self, client: PyTezosClient, custom_config=None, last_winner_payload : str | None = None) -> OperationGroup:
        """Deploys Kernel Governance"""

        metadata = Metadata.make_default(
            name='Kernel Governance',
            description='The Kernel Governance contract allows bakers to make proposals and vote on kernel upgrade',
        )

        storage = self.make_storage(metadata, custom_config, last_winner_payload)
        filename = join(get_build_dir(), 'kernel_governance.tz')

        return originate_from_file(filename, client, storage)
    

    def trigger_kernel_upgrade(self, rollup_address : str) -> ContractCall:
        """Triggers kernel upgrade transaction to rollup with last winner kernel hash"""

        return self.contract.trigger_kernel_upgrade(rollup_address)
    
    
    def new_proposal(self, sender_key_hash : str, hash : bytes) -> ContractCall:
        """Creates a new proposal"""

        return self.contract.new_proposal(
            {'sender_key_hash': sender_key_hash, 'hash': hash}
        )
    
    
    def upvote_proposal(self, sender_key_hash : str, hash : bytes) -> ContractCall:
        """Upvotes an exist proposal"""

        return self.contract.upvote_proposal(
            {'sender_key_hash': sender_key_hash, 'hash': hash}
        )
    
    def vote(self, sender_key_hash : str, vote : str) -> ContractCall:
        """Votes for a hash in promotion period"""

        return self.contract.vote(
            {'sender_key_hash': sender_key_hash, 'vote': vote}
        )
