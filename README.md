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