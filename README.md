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