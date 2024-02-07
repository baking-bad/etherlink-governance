from pytezos import pytezos
from tests.helpers.contracts.kernel_governance import KernelGovernance
from typing import Optional
import click
from scripts.environment import load_or_ask


@click.command()
@click.option(
    '--governance_contract_address',
    required=True,
    help='Contract address which contain new kernel hash',
)
@click.option(
    '--rollup_address',
    required=True,
    help='We make a transaction to the provided rollup',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def trigger_kernel_upgrade(
    governance_contract_address: str,
    rollup_address: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    private_key = private_key or load_or_ask('PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    kernelGovernance : KernelGovernance = KernelGovernance.from_address(manager, governance_contract_address)
    opg = kernelGovernance.using(manager).trigger_kernel_upgrade(rollup_address).send()
    manager.wait(opg)
    print(f'Transaction hash: {opg.hash()}')


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
    '--promotion_super_majority',
    default=10,
    help='The min promotion_super_majority for the proposal be considered as a winner, default: 10 (10%)',
)
@click.option(
    '--scale',
    default=100,
    help='For example if scale = 100 and proposal_quorum = 80 then proposal_quorum == .80 == 80%',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_kernel_governance(
    started_at_level: int,
    period_length: int,
    upvoting_limit: int,
    proposal_quorum: int,
    promotion_quorum: int,
    promotion_super_majority: int,
    scale : int,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> KernelGovernance:
    """Deploys Kernel Governance contract using provided key as a manager"""

    private_key = private_key or load_or_ask('PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    config = {
        'started_at_level': int(started_at_level),
        'period_length': int(period_length),
        'upvoting_limit': int(upvoting_limit),
        'scale': int(scale),
        'proposal_quorum': int(proposal_quorum),
        'promotion_quorum': int(promotion_quorum),
        'promotion_super_majority': int(promotion_super_majority),
    }
    opg = KernelGovernance.originate(manager, config).send()
    manager.wait(opg)
    kernelGovernance = KernelGovernance.from_opg(manager, opg)
    return kernelGovernance

