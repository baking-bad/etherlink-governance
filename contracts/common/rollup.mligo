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


let assert_kernel_root_hash_has_correct_size
        (kernel_root_hash : bytes)
        : unit =
    assert_with_error ((Bytes.length kernel_root_hash) = 33n) Errors.incorrect_kernel_root_hash_size


let get_kernel_upgrade_payload
        (kernel_root_hash : bytes)
        (activation_timestamp : timestamp)
        : bytes =
    let timestamp = timestamp_to_padded_little_endian_bytes activation_timestamp in
    // NOTE: RLP template: 0xEBA1<ROOT_HASH>88<TIMESTAMP (little endian)>
    Bytes.concats [0xEBA1; kernel_root_hash; 0x88; timestamp]


let assert_sequencer_upgrade_payload_has_correct_size
        (proposal_payload : bytes)
        : unit =
    assert_with_error ((Bytes.length proposal_payload) = 74n) Errors.incorrect_sequencer_upgrade_payload_size


let get_sequencer_upgrade_payload
        (proposal_payload : bytes)
        (activation_timestamp : timestamp)
        : bytes =
    let public_key = Bytes.sub 0n 54n proposal_payload in
    let l2_address = Bytes.sub 54n 20n proposal_payload in
    let timestamp = timestamp_to_padded_little_endian_bytes activation_timestamp in
    // NOTE: RLP template: f855B6<public key>94<l2 address>88<timestamp (little endian)>
    Bytes.concats [0xF855B6; public_key; 0x94; l2_address; 0x88; timestamp]


let decode_upgrade_payload
        (rollup_entry : t)
        : bytes =
     match rollup_entry with
        | M_right bytes -> bytes
        | M_left _ -> failwith Errors.wrong_rollup_entrypoint