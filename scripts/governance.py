from pytezos import pytezos
from tests.helpers.contracts.sequencer_governance import SequencerGovernance
from tests.helpers.contracts.kernel_governance import KernelGovernance
from typing import Optional
import click
from scripts.environment import load_or_ask
from enum import Enum

ContractType = Enum('ContractType', ['kernel_governance', 'sequencer_governance'])

def originate_contract(contract_type, manager, config, last_winner):
    if contract_type == ContractType.kernel_governance.name:
        return KernelGovernance.originate(manager, config).send()
    elif contract_type == ContractType.sequencer_governance.name:
        return SequencerGovernance.originate(manager, config).send()
    else:
        raise ValueError("Incorrect contract_type")

@click.command()
@click.option(
    '--contract',
    required=True,
    help='"kernel_governance" or "sequencer_governance"',
)
@click.option(
    '--started_at_level',
    required=True,
    help='Block at which the first period of voting will start',
)
@click.option(
    '--period_length',
    default=75,
    help='The period life-time (in blocks), default: 75',
)
@click.option(
    '--adoption_period_sec',
    default=600,
    help='The duration of the l2 adoption period counted in seconds, default: 600',
)
@click.option(
    '--upvoting_limit',
    default=20,
    help='The max number of new active proposals for each account, default: 20',
)
@click.option(
    '--proposal_quorum',
    default=10,
    help='The min proposal proposal_quorum to move the proposal to next promotion phase, default: 10 (10%)',
)
@click.option(
    '--promotion_quorum',
    default=10,
    help='The min promotion_quorum for the proposal to be considered as a winner, default: 10 (10%)',
)
@click.option(
    '--promotion_supermajority',
    default=10,
    help='The min promotion_supermajority for the proposal be considered as a winner, default: 10 (10%)',
)
@click.option(
    '--scale',
    default=100,
    help='For example if scale = 100 and proposal_quorum = 80 then proposal_quorum == .80 == 80%',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_contract(
    contract: str,
    started_at_level: int,
    period_length: int,
    adoption_period_sec: int,
    upvoting_limit: int,
    proposal_quorum: int,
    promotion_quorum: int,
    promotion_supermajority: int,
    scale: int,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> KernelGovernance:
    """Deploys Kernel Governance contract using provided key as a manager"""

    private_key = private_key or load_or_ask('PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('RPC_URL')

    config = {
        'started_at_level': int(started_at_level),
        'period_length': int(period_length),
        'adoption_period_sec': int(adoption_period_sec),
        'upvoting_limit': int(upvoting_limit),
        'scale': int(scale),
        'proposal_quorum': int(proposal_quorum),
        'promotion_quorum': int(promotion_quorum),
        'promotion_supermajority': int(promotion_supermajority),
    }
    
    manager = pytezos.using(shell=rpc_url, key=private_key)
    opg = originate_contract(contract, manager, config)
    manager.wait(opg)
    kernelGovernance = KernelGovernance.from_opg(manager, opg)
    return kernelGovernance

