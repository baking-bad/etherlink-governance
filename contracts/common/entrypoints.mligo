#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "utils.mligo" "Utils"
#import "voting.mligo" "Voting"
#import "rollup.mligo" "Rollup"
#import "events.mligo" "Events"


let new_proposal 
        (type pt)
        (sender_key_hash : key_hash)
        (payload : pt)
        (storage : pt Storage.t) 
        : operation list * pt Storage.t = 
    let voting_power = Tezos.voting_power sender_key_hash in
    let {voting_context; finished_voting} = Voting.get_voting_state storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.assert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_proposal voting_context in
    let proposer = Tezos.get_sender () in
    let updated_proposal_period = Voting.add_new_proposal_and_upvote payload proposer voting_power voting_context.proposal_period storage.config in
    let operations = match finished_voting with
        | Some event_payload -> [Events.create_voting_finished_event_operation event_payload]
        | None -> [] in
    let updated_storage = { storage with voting_context = Some { voting_context with proposal_period = updated_proposal_period } } in
    operations, updated_storage


let upvote_proposal
        (type pt)
        (sender_key_hash : key_hash)
        (payload : pt)
        (storage : pt Storage.t)
        : operation list * pt Storage.t = 
    let voting_power = Tezos.voting_power sender_key_hash in
    let {voting_context; finished_voting} = Voting.get_voting_state storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.assert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_proposal voting_context in
    let voter = Tezos.get_sender () in
    let updated_proposal_period = Voting.upvote_proposal payload voter voting_power voting_context.proposal_period storage.config in
    let operations = match finished_voting with
        | Some event_payload -> [Events.create_voting_finished_event_operation event_payload]
        | None -> [] in
    let updated_storage = { storage with voting_context = Some { voting_context with proposal_period = updated_proposal_period } } in
    operations, updated_storage


let vote
        (type pt)
        (sender_key_hash : key_hash)
        (vote : Storage.promotion_vote_t)
        (storage : pt Storage.t)
        : operation list * pt Storage.t =
    let voting_power = Tezos.voting_power sender_key_hash in
    let {voting_context; finished_voting} = Voting.get_voting_state storage in
    let _ = Utils.assert_no_xtz_in_transaction () in
    let _ = Utils.assert_sender_is_key_hash_owner sender_key_hash in
    let _ = Utils.assert_voting_power_positive voting_power in
    let _ = Voting.assert_current_period_promotion voting_context in
    let voter = Tezos.get_sender () in
    let promotion_period = Option.unopt_with_error voting_context.promotion_period Errors.promotion_period_context_not_exist in
    let updated_promotion_period = Voting.vote_promotion vote voter voting_power promotion_period in
    let operations = match finished_voting with
        | Some event_payload -> [Events.create_voting_finished_event_operation event_payload]
        | None -> [] in
    let updated_storage = { storage with voting_context = Some { voting_context with promotion_period = Some updated_promotion_period } } in
    operations, updated_storage


let trigger_rollup_upgrade
        (type pt)
        (rollup_address : address)
        (storage : pt Storage.t)
        (pack_payload : pt -> bytes)
        : operation list * pt Storage.t =
    let _ = Utils.assert_no_xtz_in_transaction () in
    let {voting_context; finished_voting} = Voting.get_voting_state storage in
    let payload = Option.unopt_with_error voting_context.last_winner_payload Errors.last_winner_payload_not_found in
    let rollup_entry = Rollup.get_entry rollup_address in
    let upgrade_params = Rollup.get_upgrade_params (pack_payload payload) in
    let upgrade_operation = Tezos.transaction upgrade_params 0tez rollup_entry in
    let operations = match finished_voting with
        | Some event_payload -> [Events.create_voting_finished_event_operation event_payload]
        | None -> [] in
    let operations = upgrade_operation :: operations in
    let updated_storage = { storage with voting_context = Some voting_context } in 
    operations, updated_storage