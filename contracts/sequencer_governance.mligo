#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/voting.mligo" "Voting"
#import "common/rollup.mligo" "Rollup"
#import "common/entrypoints.mligo" "Entrypoints"
#import "common/views.mligo" "Views"

module SequencerCommitteeGovernance = struct

    type payload_t = {
        public_key : string;
        l2_address : bytes;
    }
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t

    [@entry] 
    let new_proposal 
            (payload : payload_t)
            (storage : storage_t) 
            : return_t = 
        let _ = Rollup.assert_sequencer_upgrade_payload_has_correct_size payload.public_key payload.l2_address in
        Entrypoints.new_proposal payload storage
  

    [@entry]
    let upvote_proposal 
            (payload : payload_t)
            (storage : storage_t) 
            : return_t = 
       Entrypoints.upvote_proposal payload storage
  

    [@entry]
    let vote 
            (vote : string) 
            (storage : storage_t) 
            : return_t =
        Entrypoints.vote vote storage
  

    [@entry]
    let trigger_committee_upgrade
            (rollup_address : address)
            (storage : storage_t) 
            : return_t =
        let pack_payload = fun 
                (payload : payload_t) 
                : bytes -> 
            let activation_timestamp = Tezos.get_now () + (int storage.config.adoption_period_sec) in
            Rollup.get_sequencer_upgrade_payload payload.public_key payload.l2_address activation_timestamp in
        Entrypoints.trigger_rollup_upgrade rollup_address storage pack_payload


    [@view] 
    let get_voting_state
            (_ : unit) 
            (storage : storage_t) 
            : payload_t Views.voting_state_t = 
        Views.get_voting_state storage
end