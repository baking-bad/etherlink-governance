from pytezos.client import PyTezosClient
from tests.helpers.contracts.contract import ContractHelper
from tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
)
from pytezos.operation.group import OperationGroup
from os.path import join


class InternalTestProxy(ContractHelper):
    @classmethod
    def originate(self, client: PyTezosClient) -> OperationGroup:
        storage = None
        filename = join(get_build_dir(), 'internal_test_proxy.tz')

        return originate_from_file(filename, client, storage)
    
    def get_kernel_upgrade_payload(self, kernel_root_hash : bytes, activation_timestamp : int):
        return self.contract.get_kernel_upgrade_payload(kernel_root_hash, activation_timestamp).run_view()
    
    def get_sequencer_upgrade_payload(self, public_key : str, l2_address : bytes, activation_timestamp : int):
        return self.contract.get_sequencer_upgrade_payload(public_key, l2_address, activation_timestamp).run_view()
    
    def address_to_key_hash(self, address : str):
        return self.contract.address_to_key_hash(address).run_view()