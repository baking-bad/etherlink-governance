#import "errors.mligo" "Errors"

let assert_no_xtz_deposit
        (unit : unit)
        : unit =
    if Tezos.get_amount () > 0mutez
        then failwith Errors.xtz_deposit_disallowed 
        else unit

let asssert_sender_is_key_hash_owner      
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