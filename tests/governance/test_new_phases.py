from tests.base import BaseTestCase
from tests.helpers.utility import pkh, pack
from pytezos.contract.result import ContractCallResult

class GovernancePhasesTestCase(BaseTestCase):
    # def test_should_initialize_proposal_phase_after_origination(self) -> None:
    #     baker = self.bootstrap_baker()
    #     governance = self.deploy_governance()

    #     kernel_hash = bytes.fromhex('0101010101010101010101010101010101010101')
    #     opg = governance.using(baker).new_proposal(pkh(baker), kernel_hash, 'abc.com').send()
    #     self.bake_block()

    #     opg = baker.shell.blocks['head':].find_operation(opg.hash())
    #     result = ContractCallResult.from_operation_group(opg)[0]

    #     print(result.storage)

    def test_should_initialize_proposal_phase_after_origination(self) -> None:
        baker = self.bootstrap_baker()
        governance = self.deploy_governance()


        print(governance.contract.storage())