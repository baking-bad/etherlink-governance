#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/utils.mligo" "Utils"
#import "common/voting.mligo" "Voting"
#import "common/rollup.mligo" "Rollup"

module SequencerCommitteeGovernance = struct

    type payload_t = (address set) 
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t

    // TODO: think about adding period_index as a parameter
    type new_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
        url : string;
    }

    [@entry] 
    let new_proposal 
            (params : new_proposal_params_t)
            (storage : storage_t) 
            : return_t = 
        let voting_power = Tezos.voting_power params.sender_key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.sender_key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_period_proposal voting_context in
        let proposer = Tezos.get_sender () in
        let _ = Voting.assert_new_proposal_allowed voting_context.proposals storage.config proposer in
        let updated_proposals = Voting.add_new_proposal params.addresses params.url proposer voting_power voting_context.proposals in
        [], { storage with voting_context = { voting_context with proposals = updated_proposals } }
  
    // TODO: think about additional entrypoint - update_proposal_url

    type upvote_proposal_params_t = {
        sender_key_hash : key_hash;
        addresses : payload_t;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : storage_t) 
            : return_t = 
        let voting_power = Tezos.voting_power params.sender_key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.sender_key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_period_proposal voting_context in
        let voter = Tezos.get_sender () in
        let updated_proposals = Voting.upvote_proposal params.addresses voter voting_power voting_context.proposals in
        [], { storage with voting_context = { voting_context with proposals = updated_proposals } }
  

    type vote_params_t = {
        sender_key_hash : key_hash;
        vote : Storage.promotion_vote_t;
    }
   
    [@entry]
    let vote 
            (params : vote_params_t) 
            (storage : storage_t) 
            : return_t =
        let voting_power = Tezos.voting_power params.sender_key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.sender_key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_period_promotion voting_context in
        let voter = Tezos.get_sender () in
        let promotion = Option.unopt_with_error voting_context.promotion Errors.promotion_context_not_exist in
        let updated_promotion = Voting.vote_promotion params.vote voter voting_power promotion in
        [], { storage with voting_context = { voting_context with promotion = Some updated_promotion } }
  

    //TODO: implement
    [@entry]
    let trigger_committee_update // TODO: Think about better name
            (_rollup_address : address) // TODO: Think about passing desired kernel_hash
            (storage : storage_t) 
            : return_t =
        // let _ = Utils.assert_no_xtz_deposit () in
        // let rollup_entry = Rollup.get_entry rollup_address in
        // let voting_context = Voting.get_voting_context storage in
        // let committee = Option.unopt_with_error voting_context.last_winner_payload Errors.last_winner_hash_not_found in // TODO: Update error
        [], storage

    type extended_voting_context_t = {
        voting_context : payload_t Storage.voting_context_t;
        total_voting_power : nat;
    }

    [@view] 
    let get_voting_context
            (_ : unit) 
            (storage : storage_t) : extended_voting_context_t = 
        { 
            voting_context = Voting.get_voting_context storage;
            total_voting_power = Tezos.get_total_voting_power ();
        }

end