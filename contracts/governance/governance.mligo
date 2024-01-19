#import "storage.mligo" "Storage"
#import "phases.mligo" "Phases"
#import "errors.mligo" "Errors"
#import "utils.mligo" "Utils"
#import "voting.mligo" "Voting"

module Governance = struct

    type return_t = operation list * Storage.t

    type new_proposal_params_t = {
        key_hash : key_hash;
        hash : bytes;
        url : string;
    }

    [@entry] 
    let new_proposal 
            (params : new_proposal_params_t)
            (storage : Storage.t) 
            : return_t = 
        let voting_power = Tezos.voting_power params.key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_phase_proposal voting_context in
        let proposer = Tezos.get_sender () in
        let _ = Voting.assert_new_proposal_allowed voting_context.proposals storage.config proposer in
        let updated_proposals = Voting.add_new_proposal params.hash params.url proposer voting_power voting_context.proposals in
        [], { storage with voting_context = { voting_context with proposals = updated_proposals } }
  
    type upvote_proposal_params_t = {
        key_hash : key_hash;
        hash : bytes;
    }

    [@entry]
    let upvote_proposal 
            (params : upvote_proposal_params_t) 
            (storage : Storage.t) 
            : return_t = 
        let voting_power = Tezos.voting_power params.key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_phase_proposal voting_context in
        let voter = Tezos.get_sender () in
        let updated_proposals = Voting.upvote_proposal params.hash voter voting_power voting_context.proposals in
        [], { storage with voting_context = { voting_context with proposals = updated_proposals }}
  
    [@entry]
    let vote (_ : unit) (storage : Storage.t) : return_t = [], storage
  
    [@entry]
    let trigger_upgrade (_ : unit) (storage : Storage.t) : return_t = [], storage

end