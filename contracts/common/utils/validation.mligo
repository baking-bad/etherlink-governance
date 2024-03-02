#import "../errors.mligo" "Errors"

let assert_no_xtz_in_transaction
        (_ : unit)
        : unit =
    assert_with_error (Tezos.get_amount () = 0mutez) Errors.xtz_in_transaction_disallowed 

let assert_voting_power_positive
        (voting_power : nat)
        : unit =
    assert_with_error (voting_power > 0n) Errors.no_voting_power

let assert_proposer_allowed
        (proposer : address)
        (voting_power : nat)
        (allowed_proposers : address set)
        : unit =
    if (Set.size allowed_proposers) = 0n
        then assert_voting_power_positive voting_power
        else assert_with_error (Set.mem proposer allowed_proposers) Errors.proposer_not_allowed
