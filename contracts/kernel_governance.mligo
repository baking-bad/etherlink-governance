#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/utils.mligo" "Utils"
#import "common/voting.mligo" "Voting"
#import "common/rollup.mligo" "Rollup"
#import "common/entrypoints.mligo" "Entrypoints"

module KernelGovernance = struct

    type payload_t = bytes 
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t

    type new_proposal_params_t = {
        sender_key_hash : key_hash;
        hash : payload_t;
    }

    [@entry] 
    let new_proposal 
            (params : new_proposal_params_t)
            (storage : storage_t) 
            : return_t = 
        let preimage_hash = params.hash in
        let _ = Utils.assert_preimage_hash_has_correct_size preimage_hash in
        Entrypoints.new_proposal params.sender_key_hash preimage_hash storage
  

    type upvote_proposal_params_t = {
        sender_key_hash : key_hash;
        hash : payload_t;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : storage_t) 
            : return_t = 
       Entrypoints.upvote_proposal params.sender_key_hash params.hash storage
  

    type vote_params_t = {
        sender_key_hash : key_hash;
        vote : string;
    }
   

    [@entry]
    let vote 
            (params : vote_params_t) 
            (storage : storage_t) 
            : return_t =
        Entrypoints.vote params.sender_key_hash params.vote storage
  

    [@entry]
    let trigger_kernel_upgrade
            (rollup_address : address)
            (storage : storage_t) 
            : return_t =
        let pack_payload = fun 
                (payload : payload_t) 
                : bytes -> 
            let activation_time = Tezos.get_now () + storage.config.cooldown_period_sec in
            Rollup.get_upgrade_payload payload activation_time in
        Entrypoints.trigger_rollup_upgrade rollup_address storage pack_payload


    [@view] 
    let get_voting_state
            (_ : unit) 
            (storage : storage_t) 
            : payload_t Voting.voting_state_t = 
        Voting.get_voting_state storage


    [@view] 
    let get_period_remaining_blocks
            (_ : unit) 
            (storage : storage_t) 
            : nat = 
        Voting.get_current_period_remaining_blocks storage.config

    type upgrade_payload_params_t = {
        preimage_hash : payload_t;
        activation_timestamp : timestamp;
    }

    [@view] 
    let get_upgrade_payload
            (params: upgrade_payload_params_t) 
            (_ : storage_t) 
            : bytes = 
        let { preimage_hash; activation_timestamp } = params in
        Rollup.get_upgrade_payload preimage_hash activation_timestamp
end