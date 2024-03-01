#import "errors.mligo" "Errors"

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

let address_to_key_hash
        (address : address)
        : key_hash =
    let address_packed = Bytes.pack address in
    let key_hash_packed = Bytes.concats [(Bytes.sub 0n 5n address_packed); 0x15; (Bytes.sub 7n 21n address_packed)] in
    Option.unopt_with_error (Bytes.unpack key_hash_packed) Errors.not_implicit_address

let timestamp_to_nat
        (value : timestamp)
        : nat =
    abs (value - (0 : timestamp))

let nat_to_bytes 
        (value : nat) 
        : bytes =
    [%Michelson ({| { BYTES } |} : nat -> bytes)] value

let bytes_to_nat 
        (value : bytes) 
        : nat =
    [%Michelson ({| { NAT } |} : bytes -> nat)] value

let nat_to_little_endian_bytes
        (value : nat)
        : bytes = 
    let bytes = nat_to_bytes value in
    let mut res : bytes = 0x in
    let bytes_length = Bytes.length bytes in
    let _ = for i = 0 upto bytes_length - 1 do
        let index : nat = Option.unopt (is_nat i) in
        res := Bytes.concat (Bytes.sub index 1n bytes) res
    done in
    res

let pad_end
        (source : bytes)
        (target_length : nat)
        (pad_value : bytes)
        : bytes =
    let mut res = source in
    let source_length = int (Bytes.length source) in
    let _ = for _i = source_length upto target_length - 1 do
        res := Bytes.concat res pad_value
    done in
    res