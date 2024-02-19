#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "events.mligo" "Events"

let get_period_index
        (config : Storage.config_t)
        : nat =
    let blocks_after_start_int = Tezos.get_level () - config.started_at_level in
    match is_nat blocks_after_start_int with
        | Some blocks_after_start -> blocks_after_start / config.period_length
        | None -> failwith Errors.current_level_less_than_start_level


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


let get_upvotes_power
        (votes: (address, nat) map)
        : nat =
    let get_voting_power_sum = fun ((sum, (_, voting_power)) : (nat * (address * nat)) ) ->
        sum + voting_power in
    Map.fold get_voting_power_sum votes 0n


let get_proposal_winner
        (type pt)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt option =
        let get_winners = fun ((winner, max_power), (_, proposal) : (pt option * nat) * (bytes * pt Storage.proposal_t)) -> 
            let upvotes_power = get_upvotes_power proposal.votes in
            if upvotes_power > max_power
                then (Some(proposal.payload), upvotes_power)
                else if upvotes_power = max_power
                    then (None, max_power)
                    else (winner, max_power) in
        let (winner_payload, winner_upvotes_power) = Map.fold get_winners proposal_period.proposals (None, 0n) in
        let proposal_quorum_reached = winner_upvotes_power * config.scale >= proposal_period.total_voting_power * config.proposal_quorum in
        if proposal_quorum_reached
            then winner_payload
            else None


type aggregated_promotion_voting_power_t = {
    yay_votes_power : nat;
    nay_votes_power : nat;
    pass_votes_power : nat;
}

let get_aggregated_promotion_voting_power
        (votes: (address, Storage.promotion_vote_params_t) map)
        : aggregated_promotion_voting_power_t =
    let get_values = fun ((values), (_, vote_params) : (aggregated_promotion_voting_power_t * (address * Storage.promotion_vote_params_t) )) ->
        match vote_params.vote with
            | Yay  -> { values with yay_votes_power = values.yay_votes_power + vote_params.voting_power }
            | Nay  -> { values with nay_votes_power = values.nay_votes_power + vote_params.voting_power }
            | Pass -> { values with pass_votes_power = values.pass_votes_power + vote_params.voting_power } in
    let result = { yay_votes_power = 0n; nay_votes_power = 0n; pass_votes_power = 0n } in
    Map.fold get_values votes result


let get_promotion_winner
        (type pt)
        (promotion_period : pt Storage.promotion_period_t)
        (config : Storage.config_t)
        : pt option =
    let { total_voting_power; votes; payload; } = promotion_period in 
    let { yay_votes_power; nay_votes_power; pass_votes_power; } = get_aggregated_promotion_voting_power votes in 
    let quorum_reached = (yay_votes_power + nay_votes_power + pass_votes_power) * config.scale / total_voting_power >= config.promotion_quorum in
    let yay_nay_votes_sum = yay_votes_power + nay_votes_power in
    let super_majority_reached = if yay_nay_votes_sum > 0n
        then yay_votes_power * config.scale / yay_nay_votes_sum >= config.promotion_supermajority
        else false in
    if quorum_reached && super_majority_reached 
        then Some payload
        else None


let init_new_proposal_voting_period
        (type pt)
        (period_index : nat)
        (last_winner_payload : pt option)
        : pt Storage.voting_context_t =
    { 
        period_index = period_index;
        period_type = Proposal;
        proposal_period = {
            proposals = Map.empty;
            total_voting_power = Tezos.get_total_voting_power ();
        };
        promotion_period = None;
        last_winner_payload = last_winner_payload;
    }   


let init_new_promotion_voting_period
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (period_index : nat)
        (proposal_winner : pt)
        : pt Storage.voting_context_t =
    { 
        voting_context with 
        period_index = period_index;
        period_type = Promotion;
        promotion_period = Some {
            payload = proposal_winner;
            votes = Map.empty;
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
                | Some proposal_winner -> 
                    let next_period_index = voting_context.period_index + 1n in
                    (if period_index = next_period_index
                        then 
                            {
                                voting_context = init_new_promotion_voting_period voting_context period_index proposal_winner;
                                finished_voting = None;
                            }
                        else 
                            let voting_context_with_promotion_phase = init_new_promotion_voting_period voting_context next_period_index proposal_winner in
                            {
                                voting_context = init_new_proposal_voting_period period_index voting_context.last_winner_payload;
                                finished_voting = Some (Events.create_voting_finished_event voting_context_with_promotion_phase None);
                            })
                | None ->
                    let finished_voting = if Map.size voting_context.proposal_period.proposals > 0n 
                        then Some (Events.create_voting_finished_event voting_context None)
                        else None in
                    {
                        voting_context = init_new_proposal_voting_period period_index voting_context.last_winner_payload;
                        finished_voting = finished_voting;
                    })
        | Promotion ->
            let new_proposal_voting_context = init_new_proposal_voting_period period_index voting_context.last_winner_payload in
            let promotion_period = Option.unopt voting_context.promotion_period in
            let promotion_winner = get_promotion_winner promotion_period config in
            let finished_voting = Some (Events.create_voting_finished_event voting_context promotion_winner) in
            let updated_voting_context = (match promotion_winner with
                | Some promotion_winner -> 
                    { 
                        new_proposal_voting_context with 
                        last_winner_payload = Some promotion_winner
                    }
                | None -> new_proposal_voting_context) in
            { 
                voting_context = updated_voting_context;
                finished_voting = finished_voting;
            }


let get_voting_state
        (type pt)
        (storage : pt Storage.t)
        : pt voting_state_t = 
    let period_index = get_period_index storage.config in
    match storage.voting_context with
        | None ->  
            {
                voting_context = init_new_proposal_voting_period period_index None;
                finished_voting = None
            }
        | Some voting_context -> 
            if period_index = voting_context.period_index 
                then { voting_context = voting_context; finished_voting = None; } 
                else init_new_voting_state voting_context storage.config period_index


let assert_current_period_proposal 
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        : unit =
    match voting_context.period_type with 
        | Proposal -> unit
        | Promotion -> failwith Errors.not_proposal_period


let assert_current_period_promotion 
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        : unit =
    match voting_context.period_type with
        | Promotion -> unit
        | Proposal -> failwith Errors.not_promotion_period


let assert_upvoting_allowed
        (type pt)
        (proposals : pt Storage.proposals_t)
        (config : Storage.config_t)
        (voter : address)
        : unit =
    let get_upvotes_count = fun (acc, (_, proposal) : nat * (bytes * pt Storage.proposal_t)) ->
        if Map.mem voter proposal.votes
            then acc + 1n
            else acc in
    let upvotes_count = Map.fold get_upvotes_count proposals 0n in
    assert_with_error (upvotes_count < config.upvoting_limit) Errors.upvoting_limit_exceeded


let get_payload_key
        (type pt)
        (payload : pt)
        : bytes =
    Crypto.sha256 (Bytes.pack payload)


let add_new_proposal_and_upvote
        (type pt)
        (payload : pt)
        (proposer : address)
        (voting_power : nat)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt Storage.proposal_period_t =
    let _ = assert_upvoting_allowed proposal_period.proposals config proposer in
    let key = get_payload_key payload in
    let _ = assert_with_error (not Map.mem key proposal_period.proposals) Errors.proposal_already_created in
    let value = {
        payload = payload;
        proposer = proposer;
        votes = Map.literal [(proposer, voting_power)];
    } in
    {
        proposal_period with
        proposals = Map.add key value proposal_period.proposals
    }


let upvote_proposal
        (type pt)
        (payload : pt)
        (voter : address)
        (voting_power : nat)
        (proposal_period : pt Storage.proposal_period_t)
        (config : Storage.config_t)
        : pt Storage.proposal_period_t =
    let _ = assert_upvoting_allowed proposal_period.proposals config voter in
    let key = get_payload_key payload in
    let proposal_opt = Map.find_opt key proposal_period.proposals in
    let proposal = Option.unopt_with_error proposal_opt Errors.proposal_not_found in
    let _ = assert_with_error (not Map.mem voter proposal.votes) Errors.proposal_already_upvoted in
    let updated_proposal = { 
        proposal with
        votes = Map.add voter voting_power proposal.votes;
    } in
    {
        proposal_period with
        proposals = Map.update key (Some updated_proposal) proposal_period.proposals
    }


let vote_promotion
        (type pt)
        (vote : Storage.promotion_vote_t)
        (voter : address)
        (voting_power : nat)
        (promotion_period : pt Storage.promotion_period_t)
        : pt Storage.promotion_period_t =
    let _ = assert_with_error (not Map.mem voter promotion_period.votes) Errors.promotion_already_voted in
    let updated_votes = Map.add voter { vote = vote; voting_power = voting_power; } promotion_period.votes in
    { promotion_period with votes = updated_votes }
