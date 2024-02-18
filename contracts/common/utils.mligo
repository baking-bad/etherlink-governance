#import "errors.mligo" "Errors"

let assert_no_xtz_in_transaction
        (_ : unit)
        : unit =
    assert_with_error (Tezos.get_amount () = 0mutez) Errors.xtz_in_transaction_disallowed 

let assert_sender_is_key_hash_owner      
        (key_hash : key_hash)
        : unit =
    let address_from_key_hash = Tezos.address (Tezos.implicit_account key_hash) in
    assert_with_error (address_from_key_hash = Tezos.get_sender ()) Errors.sender_not_key_hash_owner

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

let assert_payload_not_last_winner
        (type pt)
        (payload : pt)
        (last_winner_payload_opt : pt option) =
    match last_winner_payload_opt with
        | Some last_winner_payload ->
            assert_with_error (Bytes.pack payload <> Bytes.pack last_winner_payload) Errors.payload_same_as_last_winner
        | None -> unit
