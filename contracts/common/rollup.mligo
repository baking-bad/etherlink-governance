#import "errors.mligo" "Errors"
#import "utils.mligo" "Utils"

type content_t = nat * bytes option
type ticket_t = content_t ticket
type deposit_t = bytes * ticket_t

type deposit_or_bytes_t = (
    deposit_t,
    "d",
    bytes,
    "a"
) michelson_or

type t = (
    deposit_or_bytes_t,
    "",
    bytes,
    "u"
) michelson_or

let get_entry   // NOTE: the entrypoint is used to upgrade kernel and sequencer committee as well
        (rollup : address) 
        : t contract =
    match Tezos.get_contract_opt rollup with
        | None -> failwith Errors.rollup_entrypoint_not_found
        | Some entry -> entry

let get_upgrade_params 
        (payload : bytes)
        : t =
    M_right payload

let timestamp_to_padded_little_endian_bytes
        (value : timestamp)
        : bytes =
    let timestamp_number : nat = Utils.timestamp_to_nat value in
    let timestamp_bytes = Utils.nat_to_little_endian_bytes timestamp_number in
    Utils.pad_end timestamp_bytes 8n 0x00

let get_upgrade_payload
        (preimage_hash : bytes)
        (activation_timestamp : timestamp)
        : bytes =
    let timestamp = timestamp_to_padded_little_endian_bytes activation_timestamp in
    Bytes.concats [0xEBA1; preimage_hash; 0x88; timestamp]