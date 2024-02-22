from pytezos import pytezos
from tests.helpers.contracts.kernel_governance import KernelGovernance
from typing import Optional
import click
from scripts.environment import load_or_ask


@click.command()
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
    '--cooldown_period_sec',
    default=600,
    help='The duration of the l2 cooldown period counted in seconds, default: 600',
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
@click.option(
    '--allowed_proposer',
    default=[],
    multiple=True,
    help='an accounts that can submit new proposals (if set is empty then anyone is allowed)',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_kernel_governance(
    started_at_level: int,
    period_length: int,
    cooldown_period_sec: int,
    upvoting_limit: int,
    proposal_quorum: int,
    promotion_quorum: int,
    promotion_supermajority: int,
    scale: int,
    allowed_proposer: list[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> KernelGovernance:
    """Deploys Kernel Governance contract using provided key as a manager"""

    private_key = private_key or load_or_ask('PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('RPC_URL')

    config = {
        'started_at_level': int(started_at_level),
        'period_length': int(period_length),
        'cooldown_period_sec' : int(cooldown_period_sec),
        'upvoting_limit': int(upvoting_limit),
        'scale': int(scale),
        'allowed_proposers': list(allowed_proposer),
        'proposal_quorum': int(proposal_quorum),
        'promotion_quorum': int(promotion_quorum),
        'promotion_supermajority': int(promotion_supermajority),
    }
    
    manager = pytezos.using(shell=rpc_url, key=private_key)
    opg = KernelGovernance.originate(manager, config).send()
    manager.wait(opg)
    kernelGovernance = KernelGovernance.from_opg(manager, opg)
    return kernelGovernance

