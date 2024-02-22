# Etherlink governance smart contracts

todo

## Commands

### Build
```
make compile
```
### Test
The testing stack for the contracts is based on Python and requires [poetry](https://python-poetry.org/), [pytezos](https://pytezos.org/), and [pytest](https://docs.pytest.org/en/7.4.x/) to be installed.
```
poetry run pytest
```

### Deploy Kernel Governance contract
```
poetry run deploy_kernel_governance --started_at_level 5370247 --scale 10000 --proposal_quorum 2 --promotion_quorum 2 --promotion_supermajority 5000 --rpc-url https://rpc.tzkt.io/ghostnet
```

## Deployed contracts

### Kernel Governance

| Network    | Contract address                       |
|------------|:--------------------------------------:|
| ghostnet   |  KT1JA6kdnWJqXRpKKHU5e99yuE3Yd1X5KyrL  |

# Kernel governance contract

The contract allows bakers to make proposals and vote for kernel upgrade as well as trigger kernel upgrade with the latest voting winner payload stored in the smart contract and updated through the voting process

# Entrypoints

## Proposal period

### new_proposal

Creates and upvotes a new proposal.

#### Client command

```bash
octez-client transfer 0 from %YOUR_ADDRESS% to %CONTRACT_ADDRESS% --entrypoint "new_proposal" --arg "%KERNEL_ROOT_HASH%"
```

#### Example

```bash
octez-client transfer 0 from tz1RfbwbXjE8UaRLLjZjUyxbj4KCxibTp9xN to KT1HfJb718fGszcgYguA4bfTjAqe1BEmFHkv --entrypoint "new_proposal" --arg "0x009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abc"
```

### upvote_proposal

Upvotes an existing proposal.

#### Client command

```bash
octez-client transfer 0 from %YOUR_ADDRESS% to %CONTRACT_ADDRESS% --entrypoint "upvote_proposal" --arg "%KERNEL_ROOT_HASH%"
```

#### Example

```bash
octez-client transfer 0 from tz1RfbwbXjE8UaRLLjZjUyxbj4KCxibTp9xN to KT1HfJb718fGszcgYguA4bfTjAqe1BEmFHkv --entrypoint "upvote_proposal" --arg "0x009279df4982e47cf101e2525b605fa06cd3ccc0f67d1c792a6a3ea56af9606abc"
```

## Promotion period

### vote

Votes with **yay**, **nay** or **pass** on the proposal that has advanced to the promotion period.

#### Client command

```bash
octez-client transfer 0 from %YOUR_ADDRESS% to %CONTRACT_ADDRESS%  --entrypoint "vote" --arg "\"%YOUR_VOTE%\""
```

where `%YOUR_VOTE%` is one of the values: `yay`, `nay` or `pass`

#### Example

```bash
octez-client transfer 0 from tz1RfbwbXjE8UaRLLjZjUyxbj4KCxibTp9xN to KT1HfJb718fGszcgYguA4bfTjAqe1BEmFHkv --entrypoint "vote" --arg "\"yay\""
```

## Send upgrade to kernel

### trigger_kernel_upgrade

Calls a smart rollup's upgrade entrypoint and passes the latest voting winner payload (kernel root hash). It can be called any number of times.

#### Client command

```bash
octez-client transfer 0 from %YOUR_ADDRESS% to %CONTRACT_ADDRESS% --entrypoint "trigger_kernel_upgrade" --arg "\"%SMART_ROLLUP_ADDRESS%\""
```

#### Example

```bash
octez-client transfer 0 from tz1RfbwbXjE8UaRLLjZjUyxbj4KCxibTp9xN to KT1HfJb718fGszcgYguA4bfTjAqe1BEmFHkv --entrypoint "trigger_kernel_upgrade" --arg "\"sr1EStimadnRRA3vnjpWV1RwNAsDbM3JaDt6\""
```


# The get_voting_state on-chain view and voting_finished events

**Note: Don't use the storage to get the actual state**


Use the [get_voting_state](https://better-call.dev/ghostnet/KT1JA6kdnWJqXRpKKHU5e99yuE3Yd1X5KyrL/views) view to obtain the actual state of current voting process at the time of the call. This returns the actual recalculated `voting_context` value as well as pending `voting_finished` event payload in case if the latest voting period is finished but the event was not sent to blockchain yet. The event will be sent after the next successful call to any entrypoint.

Use the [contract events](https://better-call.dev/ghostnet/KT1JA6kdnWJqXRpKKHU5e99yuE3Yd1X5KyrL/events) to see the history of voting epochs 


# Config

How to read values stored in the smart contract storage config
```ocaml
(*
    NOTE:
    started_at_level and period_length values should be chosen carefully 
    to be sure that the contract governance periods 
    never cross the boundaries of the tezos protocol governance periods. 
    This ensures the immutability of voting power throughout the entire voting period 
*)
type config_t = {
    (* 
        Used to align voting periods with protocol governance periods. 
        Should be the start level of the current protocol governance period 
    *)
    started_at_level : nat;

    (* 
        The duration of the of proposal and promotion periods represented in blocks. 
        period_length = tezos_governance_period_length / N, where N is integer divisor (factor)
    *)
    period_length : nat;

    (* 
        The duration of the l2 cooldown period counted in seconds. 
        Used to generate an upgrade payload with activation timestamp 
        on trigger_upgrade entrypoint call 
    *)
    cooldown_period_sec : int;

    (* Number of proposals that an account may upvote and submit *)
    upvoting_limit : nat;               

    (* Accounts that can submit new proposals (if set is empty then anyone is allowed) *)
    allowed_proposers : address set;

    (* 
        The scale for proposal_quorum, promotion_quorum and promotion_supermajority params. 
        For example if config.scale = 100 and config.proposal_quorum = 80 
        then proposal_quorum_% == 80 / 100 == .80 == 80%
    *)
    scale : nat;       

    (* 
        Minimum ratio of all the cumulated stake of a proposal upvotes to the total stake 
        to advance the proposal to promotion period 
    *)
    proposal_quorum : nat;     

    (* 
        Minimum ratio of all the cumulated stake of cast ballots (yay, nay, and pass ballots) 
        to the total stake to consider the proposal as a voting winner 
    *)
    promotion_quorum : nat;    

    (* 
        Minimum ratio of cumulated stake of Yay ballots to the cumulated stake 
        of Yay and Nay ballots to consider the proposal as a voting winner
    *)
    promotion_supermajority : nat;      
}
```
