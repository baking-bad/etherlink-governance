#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/utils.mligo" "Utils"
#import "common/voting.mligo" "Voting"
#import "common/rollup.mligo" "Rollup"
#import "common/entrypoints.mligo" "Entrypoints"

module SequencerCommitteeGovernance = struct

    type payload_t = (address set) 
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t

    // TODO: think about adding period_index as a parameter
    type new_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
    }

    [@entry] 
    let new_proposal 
            (params : new_proposal_params_t)
            (storage : storage_t) 
            : return_t = 
        [], Entrypoints.new_proposal params.sender_key_hash params.addresses storage
  

    type upvote_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : storage_t) 
            : return_t = 
       [], Entrypoints.upvote_proposal params.sender_key_hash params.addresses storage
  

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
    let trigger_committee_upgrade // TODO: Think about better name
            (rollup_address : address)
            (storage : storage_t) 
            : return_t =
        let addresses = Entrypoints.get_last_winner_payload storage in
        let rollup_entry = Rollup.get_entry rollup_address in
        let upgrade_params = Rollup.get_upgrade_params (Bytes.pack addresses) in
        let upgrade_operation = Tezos.transaction upgrade_params 0tez rollup_entry in 
        [upgrade_operation], storage


    [@view] 
    let get_voting_context
            (_ : unit) 
            (storage : storage_t) 
            : payload_t Voting.extended_voting_context_t = 
        Voting.get_extended_voting_context storage

end