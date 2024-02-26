from tests.base import BaseTestCase
from tests.helpers.contracts.governance_base import PROPOSAL_PERIOD, PROMOTION_PERIOD
from tests.helpers.utility import DEFAULT_TOTAL_VOTING_POWER, DEFAULT_VOTING_POWER

class KernelGovernanceProposalPeriodTestCase(BaseTestCase):
    def test_should_reset_proposals_when_no_proposals(self) -> None:
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3
        })
        assert self.get_current_level() == governance_started_at_level

        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()
        # Period index: 0. Block: 2 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }
        
        self.bake_block()
        # Period index: 0. Block: 3 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()
        # Period index: 1. Block: 1 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()
        # Period index: 1. Block: 2 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_blocks(10)
        # Period index: 4. Block: 2 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 4,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

    def test_should_reset_proposals_when_period_is_finished_with_no_votes_except_proposer(self) -> None:
        baker = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 2
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 2,
            'proposal_quorum': 40 # 1 baker out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 2
        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker).new_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()
        # Period index: 1. Block: 1 of 2
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': {
                'finished_at_period_index': 1, 
                'finished_at_period_type': PROPOSAL_PERIOD,
                'winner_payload': None
            }
        }
    
    def test_should_reset_proposals_when_period_is_finished_with_not_enough_votes(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 60 # 2 bakers out of 5 will vote
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER * 2,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': {
                'finished_at_period_index': 1, 
                'finished_at_period_type': PROPOSAL_PERIOD,
                'winner_payload': None
            }
        }

    def test_should_reset_proposals_when_period_is_finished_with_2_winners(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 20 # 1 bakers out of 5 will vote for each proposal
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_root_hash1 = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(kernel_root_hash1).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash1,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 3 of 3
        kernel_root_hash2 = bytes.fromhex('020202020202020202020202020202020202020202020202020202020202020202')
        governance.using(baker2).new_proposal(kernel_root_hash2).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }
        
        self.bake_block()

        # Period index: 1. Block: 1 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': {
                'finished_at_period_index': 1, 
                'finished_at_period_type': PROPOSAL_PERIOD,
                'winner_payload': None
            }
        }

    def test_should_reset_proposals_when_promotion_period_is_skipped(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER * 2,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_blocks(4)

        # Period index: 2. Block: 1 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 2,
                'proposal_period': {
                    'winner_candidate': None,
                    'max_upvotes_voting_power': None,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': {
                'finished_at_period_index': 2, 
                'finished_at_period_type': PROMOTION_PERIOD,
                'winner_payload': None
            }
        }

    def test_should_prolong_to_promotion_when_proposal_period_is_finished_with_a_winner(self) -> None:
        baker1 = self.bootstrap_baker()
        baker2 = self.bootstrap_baker()
        # deploying will take 1 block
        governance_started_at_level = self.get_current_level() + 1 
        # Period index: 0. Block: 1 of 3
        governance = self.deploy_kernel_governance(custom_config={
            'started_at_level': governance_started_at_level,
            'period_length': 3,
            'proposal_quorum': 40 # 2 bakers out of 5 voted
        })
        assert self.get_current_level() == governance_started_at_level

        # Period index: 0. Block: 2 of 3
        kernel_root_hash = bytes.fromhex('010101010101010101010101010101010101010101010101010101010101010101')
        governance.using(baker1).new_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        # Period index: 0. Block: 3 of 3
        governance.using(baker2).upvote_proposal(kernel_root_hash).send()
        self.bake_block()
        
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROPOSAL_PERIOD,
                'period_index': 0,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER * 2,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': None,
                'last_winner_payload': None
            },
            'finished_voting': None
        }

        self.bake_block()

        # Period index: 1. Block: 1 of 3
        assert governance.get_voting_state() == {
            'voting_context': {
                'period_type': PROMOTION_PERIOD,
                'period_index': 1,
                'proposal_period': {
                    'winner_candidate': kernel_root_hash,
                    'max_upvotes_voting_power': DEFAULT_VOTING_POWER * 2,
                    'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'promotion_period': {
                   'payload': kernel_root_hash,
                   'yay_voting_power': 0,
                   'nay_voting_power': 0,
                   'pass_voting_power': 0,
                   'total_voting_power': DEFAULT_TOTAL_VOTING_POWER
                },
                'last_winner_payload': None
            },
            'finished_voting': None
        }
