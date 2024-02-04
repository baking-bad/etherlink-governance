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
        [], Entrypoints.new_proposal params.sender_key_hash params.hash storage
  

    type upvote_proposal_params_t = {
        sender_key_hash : key_hash;
        hash : payload_t;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : storage_t) 
            : return_t = 
       [], Entrypoints.upvote_proposal params.sender_key_hash params.hash storage
  

    type vote_params_t = {
        sender_key_hash : key_hash;
        vote : Storage.promotion_vote_t;
    }
   

    [@entry]
    let vote 
            (params : vote_params_t) 
            (storage : storage_t) 
            : return_t =
        [], Entrypoints.vote params.sender_key_hash params.vote storage
  

    [@entry]
    let trigger_kernel_upgrade
            (rollup_address : address)
            (storage : storage_t) 
            : return_t =
        let kernel_hash = Entrypoints.get_last_winner_payload storage in
        let rollup_entry = Rollup.get_entry rollup_address in
        let upgrade_params = Rollup.get_upgrade_params kernel_hash in
        let upgrade_operation = Tezos.transaction upgrade_params 0tez rollup_entry in 
        [upgrade_operation], storage


    [@view] 
    let get_voting_context
            (_ : unit) 
            (storage : storage_t) 
            : payload_t Voting.extended_voting_context_t = 
        Voting.get_extended_voting_context storage

end