#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "utils.mligo" "Utils"
#import "voting.mligo" "Voting"
#import "rollup.mligo" "Rollup"

module Governance = struct

    type return_t = operation list * Storage.t

    // TODO: think about adding phase_index as a parameter
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
        [], { storage with voting_context = { voting_context with proposals = updated_proposals } }
  

    type vote_params_t = {
        key_hash : key_hash;
        vote : Storage.promotion_vote_t;
    }
   
    [@entry]
    let vote 
            (params : vote_params_t) 
            (storage : Storage.t) 
            : return_t =
        let voting_power = Tezos.voting_power params.key_hash in
        let voting_context = Voting.get_voting_context storage in
        let _ = Utils.assert_no_xtz_deposit () in
        let _ = Utils.asssert_sender_is_key_hash_owner params.key_hash in
        let _ = Utils.assert_voting_power_positive voting_power in
        let _ = Voting.assert_current_phase_promotion voting_context in
        let voter = Tezos.get_sender () in
        let promotion = Option.unopt_with_error voting_context.promotion Errors.promotion_context_not_exist in
        let updated_promotion = Voting.vote_promotion params.vote voter voting_power promotion in
        [], { storage with voting_context = { voting_context with promotion = Some updated_promotion } }
  

    [@entry]
    let trigger_kernel_upgrade // TODO: Think about better name
            (_ : unit) // TODO: Think about passing desired kernel_hash
            (storage : Storage.t) 
            : return_t =
        let _ = Utils.assert_no_xtz_deposit () in
        let rollup_entry = Rollup.get_entry storage.config.rollup_address in
        let voting_context = Voting.get_voting_context storage in
        let kernel_hash = Option.unopt_with_error voting_context.last_winner_hash Errors.last_winner_hash_not_found in
        let upgrade_params = Rollup.get_upgrade_params kernel_hash in
        let upgrade_operation = Tezos.transaction upgrade_params 0tez rollup_entry in 
        [upgrade_operation], storage

    type extended_voting_context_t = {
        voting_context : Storage.voting_context_t;
        total_voting_power : nat;
    }

    [@view] 
    let get_voting_context
            (_ : unit) 
            (storage : Storage.t) : extended_voting_context_t = 
        { 
            voting_context = Voting.get_voting_context storage;
            total_voting_power = Tezos.get_total_voting_power ();
        }

end