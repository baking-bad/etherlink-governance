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
poetry run deploy_kernel_governance
```

### Trigger Kernel Upgrade
```
poetry run trigger_kernel_upgrade
```
## Deployed contracts

### Kernel Governance

| Network    | Contract address                       |
|------------|:--------------------------------------:|
| nairobinet |  KT1C5dyTp5HhM9rp9mY6xs3SdNe1RjfFx9df  |
| weeklynet  |  N/A  |
| daylynet   |  N/A  |