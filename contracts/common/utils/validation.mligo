#import "../errors.mligo" "Errors"

let assert_no_xtz_in_transaction
        (_ : unit)
        : unit =
    assert_with_error (Tezos.get_amount () = 0mutez) Errors.xtz_in_transaction_disallowed 

let assert_voting_power_positive
        (voting_power : nat)
        : unit =
    assert_with_error (voting_power > 0n) Errors.no_voting_power


let check_proposer_in_committee 
        (proposer : address)
        (proposers_governance_contract : address)
        : bool = 
    let view_result = Tezos.call_view "check_address_in_committee" proposer proposers_governance_contract in
    match view_result with
        | Some result -> result
        | None -> failwith Errors.failed_to_check_proposer_in_committee

let assert_proposer_allowed
        (proposer : address)
        (voting_power : nat)
        (proposers_governance_contract_opt : address option)
        : unit =
    match proposers_governance_contract_opt with
        | Some proposers_governance_contract -> 
            let proposer_in_committee = check_proposer_in_committee proposer proposers_governance_contract in
            assert_with_error proposer_in_committee Errors.proposer_not_in_committee
        | None ->
            assert_voting_power_positive voting_power
