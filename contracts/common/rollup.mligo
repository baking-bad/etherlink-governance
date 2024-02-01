#import "errors.mligo" "Errors"

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
        | None -> failwith Errors.rollup_entryoint_not_found
        | Some entry -> entry

let get_upgrade_params 
        (payload : bytes)
        : t =
    M_right payload 