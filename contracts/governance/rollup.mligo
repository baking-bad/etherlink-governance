#import "errors.mligo" "Errors"

type deposit_t = (
    bytes,
    "",
    nat * bytes option ticket,
    ""
) michelson_pair 

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

let get_entry
        (rollup : address) 
        : t contract =
    match Tezos.get_contract_opt rollup with
        | None -> failwith Errors.rollup_entryoint_not_found
        | Some entry -> entry

let get_upgrade_params
        (kernel_hash : bytes)
        : t =
    M_right kernel_hash 