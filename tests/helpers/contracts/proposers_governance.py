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


class ProposersGovernance(GovernanceBase):
    @classmethod
    def originate(self, client: PyTezosClient, custom_config=None, last_winner=None) -> OperationGroup:
        """Deploys Proposers Governance contract"""

        metadata = Metadata.make_default(
            name='Security Governance Committee',
            description='The Security Governance Committee contract allows bakers to make proposals and vote on allowed proposers for security governance contract',
        )

        storage = self.make_storage(metadata, is_trigger_enabled=False, custom_config=custom_config, last_winner=last_winner)
        filename = join(get_build_dir(), 'proposers_governance.tz')

        return originate_from_file(filename, client, storage)
    
    def new_proposal(self, addresses: list[str]) -> ContractCall:
        """Creates a new proposal"""

        return self.contract.new_proposal(addresses)
    
    
    def upvote_proposal(self, addresses: list[str]) -> ContractCall:
        """Upvotes an exist proposal"""

        return self.contract.upvote_proposal(addresses)
    
    def vote(self, vote : str) -> ContractCall:
        """Votes for a hash in promotion period"""

        return self.contract.vote(vote)

    def trigger_committee_upgrade(self, rollup_address : str) -> ContractCall:
        """Triggers upgrade transaction to rollup with last winner committee addresses set"""

        return self.contract.trigger_committee_upgrade(rollup_address)

    def check_proposer_in_last_winner(self, address : str):
        return self.contract.check_proposer_in_last_winner(address).run_view()