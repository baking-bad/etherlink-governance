#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "utils.mligo" "Utils"
#import "voting.mligo" "Voting"
#import "rollup.mligo" "Rollup"


let new_proposal 
        (type pt)
        (sender_key_hash : key_hash)
        (payload : pt)
        (storage : pt Storage.t) 
        : pt Storage.t = 
    let voting_power = Tezos.voting_power sender_key_hash in
    let voting_context = Voting.get_voting_context storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.asssert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_proposal voting_context in
    let proposer = Tezos.get_sender () in
    let updated_proposals = Voting.add_new_proposal payload proposer voting_power voting_context.proposals storage.config in
    { storage with voting_context = { voting_context with proposals = updated_proposals } }


let upvote_proposal
        (type pt)
        (sender_key_hash : key_hash)
        (payload : pt)
        (storage : pt Storage.t)
        : pt Storage.t = 
    let voting_power = Tezos.voting_power sender_key_hash in
    let voting_context = Voting.get_voting_context storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.asssert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_proposal voting_context in
    let voter = Tezos.get_sender () in
    let updated_proposals = Voting.upvote_proposal payload voter voting_power voting_context.proposals in
    { storage with voting_context = { voting_context with proposals = updated_proposals } }


let vote
        (type pt)
        (sender_key_hash : key_hash)
        (vote : Storage.promotion_vote_t)
        (storage : pt Storage.t)
        : pt Storage.t =
    let voting_power = Tezos.voting_power sender_key_hash in
    let voting_context = Voting.get_voting_context storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.asssert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_promotion voting_context in
    let voter = Tezos.get_sender () in
    let promotion = Option.unopt_with_error voting_context.promotion Errors.promotion_context_not_exist in
    let updated_promotion = Voting.vote_promotion vote voter voting_power promotion in
    { storage with voting_context = { voting_context with promotion = Some updated_promotion } }


let get_last_winner_payload
        (type pt)
        (storage : pt Storage.t) 
        : pt =
    let _ = Utils.assert_no_xtz_in_transaction () in
    let voting_context = Voting.get_voting_context storage in
    Option.unopt_with_error voting_context.last_winner_payload Errors.last_winner_payload_not_found
