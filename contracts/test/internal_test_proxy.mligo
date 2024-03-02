#import "../common/rollup.mligo" "Rollup"

module InternalTestProxy = struct
    (* The contract is used to test common internal functions *)

    type storage_t = unit
    type result_t = operation list * storage_t


    [@entry]
    let default
            (_ : unit)
            (storage : storage_t)
            : result_t =
        [], storage


    type kernel_upgrade_payload_params_t = {
        kernel_root_hash : bytes;
        activation_timestamp : timestamp;
    }

    [@view] 
    let get_kernel_upgrade_payload
            (params: kernel_upgrade_payload_params_t) 
            (_ : storage_t) 
            : bytes = 
        let { kernel_root_hash; activation_timestamp } = params in
        let _ = Rollup.assert_kernel_root_hash_has_correct_size kernel_root_hash in
        Rollup.get_kernel_upgrade_payload kernel_root_hash activation_timestamp

        
    type sequencer_upgrade_payload_params_t = {
        public_key : string;
        l2_address : bytes;
        activation_timestamp : timestamp;
    }

    [@view] 
    let get_sequencer_upgrade_payload
            (params: sequencer_upgrade_payload_params_t) 
            (_ : storage_t) 
            : bytes = 
        let { public_key; l2_address; activation_timestamp } = params in
        let _ = Rollup.assert_sequencer_upgrade_payload_has_correct_size public_key l2_address in
        Rollup.get_sequencer_upgrade_payload public_key l2_address activation_timestamp
end