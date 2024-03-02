#import "errors.mligo" "Errors"
#import "utils/converters.mligo" "Converters"
#import "utils/rlp.mligo" "RLP"
#import "utils/byte_utils.mligo" "ByteUtils"
#import "utils/converters.mligo" "Converters"

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
    let timestamp_number : nat = Converters.timestamp_to_nat value in
    let timestamp_bytes = Converters.nat_to_little_endian_bytes timestamp_number in
    ByteUtils.pad_end timestamp_bytes 8n 0x00


let assert_kernel_root_hash_has_correct_size
        (kernel_root_hash : bytes)
        : unit =
    assert_with_error ((Bytes.length kernel_root_hash) = 33n) Errors.incorrect_kernel_root_hash_size


let get_kernel_upgrade_payload
        (kernel_root_hash : bytes)
        (activation_timestamp : timestamp)
        : bytes =
    let timestamp_bytes = timestamp_to_padded_little_endian_bytes activation_timestamp in
    RLP.encode_list [kernel_root_hash ; timestamp_bytes]


let assert_sequencer_upgrade_payload_has_correct_size
        (public_key : string)
        (l2_address : bytes)
        : unit =
    let public_key_length = String.length public_key in
    let _ = assert_with_error ((public_key_length = 54n) || (public_key_length = 55n)) Errors.incorrect_public_key_size in
    assert_with_error ((Bytes.length l2_address) = 20n) Errors.incorrect_l2_address_size


let public_key_to_bytes
        (public_key : string)
        : bytes =
    let michelson_bytes = Bytes.pack public_key in
    let length = Converters.bytes_to_nat (Bytes.sub 2n 4n michelson_bytes) in
    Bytes.sub 6n length michelson_bytes


let get_sequencer_upgrade_payload
        (public_key : string)
        (l2_address : bytes)
        (activation_timestamp : timestamp)
        : bytes =
    let public_key_bytes = public_key_to_bytes public_key in
    let timestamp_bytes = timestamp_to_padded_little_endian_bytes activation_timestamp in
    RLP.encode_list [public_key_bytes ; l2_address ; timestamp_bytes]


let decode_upgrade_payload
        (rollup_entry : t)
        : bytes =
     match rollup_entry with
        | M_right bytes -> bytes
        | M_left _ -> failwith Errors.wrong_rollup_entrypoint