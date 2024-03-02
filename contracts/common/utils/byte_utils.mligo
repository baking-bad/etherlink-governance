#import "../errors.mligo" "Errors"

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