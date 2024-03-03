#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "events.mligo" "Events"
#import "constants.mligo" "Constants"


let get_period_index
        (config : Storage.config_t)
        : nat =
    let blocks_after_start_int = Tezos.get_level () - config.started_at_level in
    match is_nat blocks_after_start_int with
        | Some blocks_after_start -> blocks_after_start / config.period_length
        | None -> failwith Errors.current_level_less_than_start_level


[@inline]
let get_current_period_remaining_blocks
        (config : Storage.config_t)
        : nat =
    let blocks_after_start_int = Tezos.get_level () - config.started_at_level in
    let period_length = config.period_length in
    match is_nat blocks_after_start_int with
        | Some blocks_after_start ->
            let remainder = blocks_after_start mod period_length in
            Option.unopt (is_nat (period_length - remainder))
        | None -> failwith Errors.current_level_less_than_start_level


[@inline]
let get_proposal_winner
        (type pt)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt option =
        let winner_payload = proposal_period.winner_candidate in
        let winner_upvotes_power = match proposal_period.max_upvotes_voting_power with 
            | Some value -> value
            | None -> 0n in
        let proposal_quorum_reached = winner_upvotes_power * config.scale >= proposal_period.total_voting_power * config.proposal_quorum in
        if proposal_quorum_reached
            then winner_payload
            else None


[@inline]
let get_promotion_winner
        (type pt)
        (winner_candidate : pt option)
        (promotion_period : Storage.promotion_period_t)
        (config : Storage.config_t)
        : pt option =
    let { total_voting_power; yea_voting_power; nay_voting_power; pass_voting_power; voters = _} = promotion_period in 
    let quorum_reached = (yea_voting_power + nay_voting_power + pass_voting_power) * config.scale >= config.promotion_quorum * total_voting_power in
    let yea_nay_voting_sum = yea_voting_power + nay_voting_power in
    let super_majority_reached = if yea_nay_voting_sum > 0n
        then yea_voting_power * config.scale >= config.promotion_supermajority * yea_nay_voting_sum
        else false in
    if quorum_reached && super_majority_reached 
        then winner_candidate
        else None


[@inline]
let get_new_proposal_period_content
        (type pt)
        (_ : unit)
        : pt Storage.proposal_period_t =
    {
        proposals = Big_map.empty;
        upvoters_upvotes_count = Big_map.empty;
        upvoters_proposals = Big_map.empty;
        max_upvotes_voting_power = None; 
        winner_candidate = None;
        total_voting_power = Tezos.get_total_voting_power ();
    }


[@inline]
let init_new_proposal_voting_period
        (type pt)
        (period_index : nat)
        (voting_context : pt Storage.voting_context_t)
        : pt Storage.voting_context_t =
    { 
        voting_context with
        period_index = period_index;
        period_type = Proposal;
        proposal_period = (get_new_proposal_period_content ());
        promotion_period = None;
    }   


[@inline]
let init_new_promotion_voting_period
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (period_index : nat)
        : pt Storage.voting_context_t =
    { 
        voting_context with 
        period_index = period_index;
        period_type = Promotion;
        promotion_period = Some {
            voters = Big_map.empty;
            yea_voting_power = 0n;
            nay_voting_power = 0n; 
            pass_voting_power = 0n;
            total_voting_power = Tezos.get_total_voting_power ();
        }
    }   


type 'pt voting_state_t = {
    voting_context : 'pt Storage.voting_context_t;
    finished_voting : 'pt Events.voting_finished_event_payload_t option;
}

let init_new_voting_state
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (config : Storage.config_t)
        (period_index : nat)
        : pt voting_state_t =
    match voting_context.period_type with
        | Proposal -> 
            (match get_proposal_winner voting_context.proposal_period config with
                | Some _proposal_winner -> 
                    let promotion_period_index = voting_context.period_index + 1n in
                    (if period_index = promotion_period_index
                        then 
                            {
                                voting_context = init_new_promotion_voting_period voting_context period_index;
                                finished_voting = None;
                            }
                        else 
                            {
                                voting_context = init_new_proposal_voting_period period_index voting_context;
                                finished_voting = Some (Events.create_voting_finished_event promotion_period_index Promotion None);
                            })
                | None ->
                    let at_least_one_proposal_was_submitted = Option.is_some voting_context.proposal_period.max_upvotes_voting_power in
                    let finished_voting = if at_least_one_proposal_was_submitted
                        then Some (Events.create_voting_finished_event voting_context.period_index voting_context.period_type None)
                        else None in
                    {
                        voting_context = init_new_proposal_voting_period period_index voting_context;
                        finished_voting = finished_voting;
                    })
        | Promotion ->
            let promotion_period = Option.value_with_error Errors.promotion_period_not_found voting_context.promotion_period in
            let promotion_winner = get_promotion_winner voting_context.proposal_period.winner_candidate promotion_period config in
            let finished_voting = Some (Events.create_voting_finished_event voting_context.period_index voting_context.period_type promotion_winner) in
            { 
                voting_context = init_new_proposal_voting_period period_index voting_context;
                finished_voting = finished_voting;
            }


let init_voting_context
        (type pt)
        (period_index : nat)
        : pt Storage.voting_context_t = 
    {
        period_index = period_index;
        period_type = Proposal;
        proposal_period = get_new_proposal_period_content ();
        promotion_period = None;
    }


type 'pt extended_voting_state_t = {
    voting_context : 'pt Storage.voting_context_t;
    last_winner : 'pt Storage.voting_winner_t option;
    finished_voting : 'pt Events.voting_finished_event_payload_t option;
}

let get_voting_state
        (type pt)
        (storage : pt Storage.t)
        : pt extended_voting_state_t = 
    let period_index = get_period_index storage.config in
    let voting_state = match storage.voting_context with
        | None ->  
            {
                voting_context = init_voting_context period_index;
                finished_voting = None
            }
        | Some voting_context -> 
            if period_index = voting_context.period_index 
                then { voting_context = voting_context; finished_voting = None; } 
                else init_new_voting_state voting_context storage.config period_index in
    let { voting_context; finished_voting } = voting_state in
    {
        voting_context = voting_context;
        finished_voting = finished_voting;
        last_winner = match finished_voting with
            | Some event -> (match event.winner_proposal_payload with
                | Some winner_payload -> 
                    Some {
                        payload = winner_payload;
#if TRIGGER_ENABLED
                        trigger_history = Big_map.empty;
#endif
                    }
                | None -> storage.last_winner)
            | None -> storage.last_winner
    }


[@inline]
let assert_current_period_proposal 
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        : unit =
    match voting_context.period_type with 
        | Proposal -> unit
        | Promotion -> failwith Errors.not_proposal_period


[@inline]
let assert_current_period_promotion 
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        : unit =
    match voting_context.period_type with
        | Promotion -> unit
        | Proposal -> failwith Errors.not_promotion_period


[@inline]
let assert_upvoting_allowed
        (upvoters_upvotes_count : Storage.upvoters_upvotes_count_t)
        (config : Storage.config_t)
        (voter : address)
        : unit =
    let upvotes_count = match Big_map.find_opt voter upvoters_upvotes_count with
        | Some count -> count
        | None -> 0n in
    assert_with_error (upvotes_count < config.upvoting_limit) Errors.upvoting_limit_exceeded


[@inline]
let assert_vote_value_correct
        (vote : string)
        : unit =
    let value_is_correct = (vote = Constants.yea or vote = Constants.nay or vote = Constants.pass) in
    assert_with_error value_is_correct Errors.incorrect_vote_value


[@inline]
let get_payload_key
        (type pt)
        (payload : pt)
        : Storage.payload_key_t =
    Bytes.pack payload


[@inline]
let add_proposal_to_upvoter
        (upvoter : address)
        (payload_key : Storage.payload_key_t)
        (upvoters_proposals : Storage.upvoters_proposals_t)
        : Storage.upvoters_proposals_t =
    Big_map.add (upvoter, payload_key ) unit upvoters_proposals


[@inline]
let increment_upvotes_count
        (upvoter : address)
        (upvoters_upvotes_count : Storage.upvoters_upvotes_count_t)
        : Storage.upvoters_upvotes_count_t =
    match Big_map.find_opt upvoter upvoters_upvotes_count with
        | Some count -> Big_map.update upvoter (Some (count + 1n)) upvoters_upvotes_count
        | None -> Big_map.add upvoter 1n upvoters_upvotes_count


[@inline]
let update_winner_candidate
        (type pt)
        (upvotes_voting_power : nat)
        (payload : pt)
        (proposal_period : pt Storage.proposal_period_t)
        : pt Storage.proposal_period_t =
    match proposal_period.max_upvotes_voting_power with
        | Some max_upvotes_voting_power -> 
            if upvotes_voting_power > max_upvotes_voting_power
            then
                {
                    proposal_period with
                    max_upvotes_voting_power = Some upvotes_voting_power;
                    winner_candidate = Some payload 
                }
            else if upvotes_voting_power = max_upvotes_voting_power
                then 
                {
                    proposal_period with
                    winner_candidate = None 
                }
                else
                    proposal_period
        | None -> 
                {
                    proposal_period with
                    max_upvotes_voting_power = Some upvotes_voting_power;
                    winner_candidate = Some payload 
                }


[@inline]
let add_new_proposal_and_upvote
        (type pt)
        (payload : pt)
        (proposer : address)
        (voting_power : nat)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt Storage.proposal_period_t =
    let upvoters_upvotes_count = proposal_period.upvoters_upvotes_count in
    let _ = assert_upvoting_allowed upvoters_upvotes_count config proposer in
    let key = get_payload_key payload in
    let _ = assert_with_error (not Big_map.mem key proposal_period.proposals) Errors.proposal_already_created in
    let value = {
        payload = payload;
        proposer = proposer;
        upvotes_voting_power = voting_power;
    } in
    let updated_proposal_period = {
        proposal_period with
        upvoters_upvotes_count = increment_upvotes_count proposer upvoters_upvotes_count;
        upvoters_proposals = add_proposal_to_upvoter proposer key proposal_period.upvoters_proposals;
        proposals = Big_map.add key value proposal_period.proposals
    } in
    update_winner_candidate voting_power payload updated_proposal_period


[@inline]
let assert_proposal_not_already_upvoted
        (upvoter : address)
        (payload_key : Storage.payload_key_t)
        (upvoters_proposals : Storage.upvoters_proposals_t)
        : unit =
    assert_with_error (not Big_map.mem (upvoter, payload_key) upvoters_proposals) Errors.proposal_already_upvoted


[@inline]
let upvote_proposal
        (type pt)
        (payload : pt)
        (upvoter : address)
        (voting_power : nat)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt Storage.proposal_period_t =
    let upvoters_upvotes_count = proposal_period.upvoters_upvotes_count in
    let _ = assert_upvoting_allowed upvoters_upvotes_count config upvoter in
    let key = get_payload_key payload in
    let proposal = match Big_map.find_opt key proposal_period.proposals with 
        | Some value -> value 
        | None -> failwith Errors.proposal_not_found in
    let upvoters_proposals = proposal_period.upvoters_proposals in
    let _ = assert_proposal_not_already_upvoted upvoter key upvoters_proposals in
    let upvotes_voting_power = proposal.upvotes_voting_power + voting_power in
    let updated_proposal = { 
        proposal with
        upvotes_voting_power = upvotes_voting_power
    } in
    let updated_proposal_period = {
        proposal_period with
        upvoters_upvotes_count = increment_upvotes_count upvoter upvoters_upvotes_count;
        upvoters_proposals = add_proposal_to_upvoter upvoter key upvoters_proposals;
        proposals = Big_map.update key (Some updated_proposal) proposal_period.proposals;
    } in
    update_winner_candidate upvotes_voting_power payload updated_proposal_period


[@inline]
let vote_promotion
        (vote : string)
        (voter : address)
        (voting_power : nat)
        (promotion_period :Storage.promotion_period_t)
        : Storage.promotion_period_t =
    let _ = assert_with_error (not Big_map.mem voter promotion_period.voters) Errors.promotion_already_voted in
    let _ = assert_vote_value_correct vote in
    let updated_promotion_period = if vote = Constants.yea
        then { promotion_period with yea_voting_power = promotion_period.yea_voting_power + voting_power }
        else if vote = Constants.nay 
            then { promotion_period with nay_voting_power = promotion_period.nay_voting_power + voting_power }
            else { promotion_period with pass_voting_power = promotion_period.pass_voting_power + voting_power } in
    { 
        updated_promotion_period with 
        voters = Big_map.add voter unit promotion_period.voters
    }
