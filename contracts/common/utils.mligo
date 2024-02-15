#import "errors.mligo" "Errors"

let assert_no_xtz_in_transaction
        (unit : unit)
        : unit =
    if Tezos.get_amount () > 0mutez
        then failwith Errors.xtz_in_transaction_disallowed 
        else unit

let assert_sender_is_key_hash_owner      
        (key_hash : key_hash)
        : unit =
    let address_from_key_hash = Tezos.address (Tezos.implicit_account key_hash) in
    if address_from_key_hash = Tezos.get_sender ()
        then unit
        else failwith Errors.sender_not_key_hash_owner

let assert_voting_power_positive
        (voting_power : nat)
        : unit =
    if voting_power > 0n
        then unit
        else failwith Errors.no_voting_power

let assert_proposer_allowed
        (proposer : address)
        (voting_power : nat)
        (allowed_proposers : address set)
        : unit =
    if (Set.size allowed_proposers) = 0n
        then assert_voting_power_positive voting_power
        else if Set.mem proposer allowed_proposers
            then unit
            else failwith Errors.proposer_not_allowed