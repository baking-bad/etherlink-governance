#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/utils.mligo" "Utils"
#import "common/voting.mligo" "Voting"
#import "common/rollup.mligo" "Rollup"
#import "common/entrypoints.mligo" "Entrypoints"

module SequencerCommitteeGovernance = struct

    type payload_t = (address set) // TODO: think about l2 addresses as well (in the future); should we limit the size of the set?
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t

    type new_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
    }

    [@entry] 
    let new_proposal 
            (params : new_proposal_params_t)
            (storage : storage_t) 
            : return_t = 
        Entrypoints.new_proposal params.sender_key_hash params.addresses storage
  

    type upvote_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : storage_t) 
            : return_t = 
       Entrypoints.upvote_proposal params.sender_key_hash params.addresses storage
  

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
    let trigger_committee_upgrade
            (rollup_address : address)
            (storage : storage_t) 
            : return_t =
        Entrypoints.trigger_rollup_upgrade rollup_address storage (fun addresses -> Bytes.pack addresses)


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
end