#import "converters.mligo" "Converters"
#import "../errors.mligo" "Errors"

let encode_item
        (value : bytes)
        : bytes =
    let length = Bytes.length value in
    let prefix = if length <= 55n
        then 
            Converters.nat_to_bytes (length + 128n) 
        else 
            let length_bytes = Converters.nat_to_bytes length in
            let length_of_length = Bytes.length length_bytes in
            Bytes.concats [Converters.nat_to_bytes (length_of_length + 183n); length_bytes] in
    Bytes.concat prefix value

let encode_list
        (items : bytes list)
        : bytes =
    let get_list_body (acc, i: bytes * bytes) = Bytes.concat acc (encode_item i) in
    let list_body = List.fold_left get_list_body 0x items in
    let list_length = Bytes.length list_body in
    let prefix = if list_length <= 55n
        then 
            Converters.nat_to_bytes (list_length + 192n)
        else
            let list_length_bytes = Converters.nat_to_bytes list_length in
            let length_of_list_length = Bytes.length list_length_bytes in
            Bytes.concats [Converters.nat_to_bytes (length_of_list_length + 247n); list_length_bytes] in
    Bytes.concat prefix list_body
