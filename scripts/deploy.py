from pytezos import pytezos
from tests.helpers.contracts.kernel_governance import KernelGovernance
from typing import Optional
import click
from scripts.environment import load_or_ask


@click.command()
@click.option(
    '--started_at_block',
    required=True,
    help='Block at which the first period of voting will start',
)
@click.option(
    '--period_length',
    default=75,
    help='The period life-time (in blocks), default: 75',
)
@click.option(
    '--proposals_limit_per_account',
    default=20,
    help='The max number of new active proposals for each account, default: 20',
)
@click.option(
    '--min_proposal_quorum',
    default=10,
    help='The min proposal quorum to move the proposal to next promotion phase, default: 10 (10%)',
)
@click.option(
    '--quorum',
    default=10,
    help='The min quorum for the proposal to be considered as a winner, default: 10 (10%)',
)
@click.option(
    '--super_majority',
    default=10,
    help='The min super_majority for the proposal be considered as a winner, default: 10 (10%)',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_kernel_governance(
    started_at_block: int,
    period_length: int,
    proposals_limit_per_account: int,
    min_proposal_quorum: int,
    quorum: int,
    super_majority: int,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> KernelGovernance:
    """Deploys Kernel Governance contract using provided key as a manager"""

    private_key = private_key or load_or_ask('PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    config = {
        'started_at_block': int(started_at_block),
        'period_length': int(period_length),
        'proposals_limit_per_account': int(proposals_limit_per_account),
        'min_proposal_quorum': int(min_proposal_quorum),
        'quorum': int(quorum),
        'super_majority': int(super_majority),
    }
    opg = KernelGovernance.originate(manager, config).send()
    manager.wait(opg)
    kernelGovernance = KernelGovernance.from_opg(manager, opg)
    return kernelGovernance

