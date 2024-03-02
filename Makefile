LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:1.3.0

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	@if [ ! -d ./build/test ]; then mkdir ./build/test ; fi
	${LIGO_COMPILER} compile contract contracts/kernel_governance.mligo -m KernelGovernance -o build/kernel_governance.tz
	${LIGO_COMPILER} compile contract contracts/sequencer_governance.mligo -m SequencerCommitteeGovernance -o build/sequencer_governance.tz
	${LIGO_COMPILER} compile contract contracts/security_governance_committee.mligo -m SecurityGovernanceCommittee -o build/security_governance_committee.tz
	${LIGO_COMPILER} compile contract contracts/test/rollup_mock.mligo -m RollupMock -o build/test/rollup_mock.tz
	${LIGO_COMPILER} compile contract contracts/test/internal_test_proxy.mligo -m InternalTestProxy -o build/test/internal_test_proxy.tz