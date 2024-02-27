import secrets
from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import YAY_VOTE
from tests.helpers.operation_result_recorder import OperationResultRecorder
from tests.helpers.utility import find_op_by_hash, get_tests_dir
from os.path import join

class KernelGovernanceGasConsumptionTestCase(BaseTestCase):
    recorder = OperationResultRecorder()

    @classmethod
    def tearDownClass(self) -> None:
        self.recorder.write_to_file(join(get_tests_dir(), 'gas_consumption.json'))
        super().tearDownClass()

    def test_new_proposal_same_baker(self) -> None:
        baker = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 500,
            'upvoting_limit': 500,
        })

        for i in range(4):
            random_bytes = secrets.token_bytes(33)
            opg = governance.using(baker).new_proposal(random_bytes).send()
            self.bake_block()
            op = find_op_by_hash(self.manager, opg)
            self.recorder.add_element(f'new_proposal_same_baker_nth_{i + 1}', op)

    def test_new_proposal_different_baker(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        baker4 = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 500,
            'upvoting_limit': 500,
        })

        for i, baker in enumerate([baker1, baker2, baker3, baker4]):
            random_bytes = secrets.token_bytes(33)
            opg = governance.using(baker).new_proposal(random_bytes).send()
            self.bake_block()
            op = find_op_by_hash(self.manager, opg)
            self.recorder.add_element(f'new_proposal_different_baker_nth_{i + 1}', op)

    def test_new_proposal_with_event(self) -> None:
        baker1 = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 20, # 1 baker out of 5 will vote,
            'promotion_quorum': 20, # 1 bakers out of 5 will vote (20%)  
            'promotion_supermajority': 50, # 1 baker will vote yay
        })

        random_bytes = secrets.token_bytes(33)
        governance.using(baker1).new_proposal(random_bytes).send()
        self.bake_blocks(2)
        
        governance.using(baker1).vote(YAY_VOTE).send()
        self.bake_blocks(2)
        
        opg = governance.using(baker1).new_proposal(secrets.token_bytes(33)).send()
        self.bake_block()
        op = find_op_by_hash(self.manager, opg)
        self.recorder.add_element(f'test_new_proposal_with_event', op)
        
    def test_upvote_proposal(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        baker4 = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 500,
        })

        random_bytes = secrets.token_bytes(33)
        governance.using(baker1).new_proposal(random_bytes).send()
        self.bake_block()
        
        for i, baker in enumerate([baker2, baker3, baker4]):
            opg = governance.using(baker).upvote_proposal(random_bytes).send()
            self.bake_block()
            op = find_op_by_hash(self.manager, opg)
            self.recorder.add_element(f'upvote_nth_{i + 1}', op)

    def test_vote_proposal(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        baker3 = self.bootstrap_baker()
        baker4 = self.bootstrap_baker()
        governance_started_at_level = self.get_current_level() + 1
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 10,
            'proposal_quorum': 20 # 1 baker out of 5 will vote
        })

        random_bytes = secrets.token_bytes(33)
        governance.using(baker1).new_proposal(random_bytes).send()
        self.bake_blocks(11)
        
        for i, baker in enumerate([baker1, baker2, baker3, baker4]):
            opg = governance.using(baker).vote(YAY_VOTE).send()
            self.bake_block()
            op = find_op_by_hash(self.manager, opg)
            self.recorder.add_element(f'vote_nth_{i + 1}', op)
        
    # def test_new_proposal_stress(self) -> None:
    #     baker = self.bootstrap_baker()
    #     governance_started_at_level = self.get_current_level() + 1
    #     governance = self.deploy_kernel_governance(custom_config={
    #         'started_at_level': governance_started_at_level,
    #         'period_length': 5000,
    #         'upvoting_limit': 5000,
    #     })

    #     for i in range(500):
    #         random_bytes = secrets.token_bytes(30000)
    #         opg = governance.using(baker).new_proposal(random_bytes).send()
    #         self.bake_block()
    #         op = find_op_by_hash(self.manager, opg)
    #         consumed_gas = OperationResult.consumed_gas(op)
    #         print('new proposal: ', i, 'consumed_gas', consumed_gas)