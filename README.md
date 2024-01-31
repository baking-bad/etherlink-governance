# Etherlink governance smart contracts

todo

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
poetry run deploy_kernel_governance
```
#### Example
```
poetry run deploy_kernel_governance --started_at_block 2926576
```

### Trigger Kernel Upgrade
```
poetry run trigger_kernel_upgrade
```
#### Example
```
poetry run trigger_kernel_upgrade --governance_contract_address KT1GhARSyMVChJXoo8pUfPzgqGU7c5hsuVtE --rollup_address sr1BQvjNrvPLjPTHTTKLFNY6cNHrWFxc9wjB
```