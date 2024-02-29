from tests.base import BaseTestCase

class CommitteeGovernanceUpgradePayloadTestCase(BaseTestCase):
    def test_generate_correct_payload(self) -> None:
        governance = self.deploy_sequencer_governance()

        public_key = '6564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d385764397344564339796176' # edpkuBknW28nW72KG6RoHtYW7p12T6GKc7nAbwYX5m8Wd9sDVC9yav
        l2_address = '71c7656ec7ab88b098defb751b7401b5f6d8976f'
        activation_timestamp = 1709355827
        proposal_payload = bytes.fromhex(f'{public_key}{l2_address}')
        expected_upgrade_payload = 'f855b66564706b75426b6e5732386e5737324b4736526f48745957377031325436474b63376e4162775958356d3857643973445643397961769471c7656ec7ab88b098defb751b7401b5f6d8976f8833b3e26500000000'
        assert governance.get_upgrade_payload(proposal_payload, activation_timestamp).hex() == expected_upgrade_payload
    