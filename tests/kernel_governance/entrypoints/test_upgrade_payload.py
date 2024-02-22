from tests.base import BaseTestCase

class KernelGovernanceUpgradePayloadTestCase(BaseTestCase):
    def test_generate_correct_payload(self) -> None:
        governance = self.deploy_kernel_governance()

        kernel_root_hash = bytes.fromhex('009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abc')
        activation_timestamp = 1708444800
        expected_upgrade_payload = 'eba1009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abc8880ccd46500000000'
        assert governance.get_upgrade_payload(kernel_root_hash, activation_timestamp).hex() == expected_upgrade_payload