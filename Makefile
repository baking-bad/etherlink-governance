LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:1.2.0

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	${LIGO_COMPILER} compile contract contracts/kernel_governance.mligo -m KernelGovernance -o build/kernel_governance.tz
	${LIGO_COMPILER} compile contract contracts/committee_governance.mligo -m SequencerCommitteeGovernance -o build/committee_governance.tz