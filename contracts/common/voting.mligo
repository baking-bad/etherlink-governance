#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"
#import "events.mligo" "Events"

let get_period_index
        (config : Storage.config_t)
        : nat =
    let blocks_after_start_int = Tezos.get_level () - config.started_at_level in
    match is_nat blocks_after_start_int with
        | Some blocks_after_start -> blocks_after_start / config.period_length
        | None -> failwith Errors.current_level_is_less_than_start_level


let get_proposal_winner
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (current_period_index : nat)
        (config : Storage.config_t)
        : pt option =
    if current_period_index = voting_context.period_index + 1n
        then
            let proposal_period = voting_context.proposal_period in
            let get_winners = fun ((winner, max_power), (_, proposal) : (pt option * nat) * (bytes * pt Storage.proposal_t)) -> 
                if proposal.upvotes_power > max_power
                    then (Some(proposal.payload), proposal.upvotes_power)
                    else if proposal.upvotes_power = max_power
                        then (None, max_power)
                        else (winner, max_power) in
            let (winner_payload, winner_upvotes_power) = Map.fold get_winners proposal_period.proposals (None, 0n) in
            let proposal_quorum_reached = winner_upvotes_power * config.scale >= proposal_period.total_voting_power * config.proposal_quorum in
            if proposal_quorum_reached
                then winner_payload
                else None
        else None


let get_promotion_winner
        (type pt)
        (promotion_period : pt Storage.promotion_period_t)
        (config : Storage.config_t)
        : pt option =
    let { yay_votes_power; nay_votes_power; pass_votes_power; payload; total_voting_power; voters = _; } = promotion_period in 
    let quorum_reached = (yay_votes_power + nay_votes_power + pass_votes_power) * config.scale / total_voting_power >= config.promotion_quorum in
    let yay_nay_votes_sum = yay_votes_power + nay_votes_power in
    let super_majority_reached = if yay_nay_votes_sum > 0n
        then yay_votes_power * config.scale / yay_nay_votes_sum >= config.promotion_super_majority
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
            total_voting_power = Tezos.get_total_voting_power ()
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
            voters = Set.empty;
            yay_votes_power = 0n;
            nay_votes_power = 0n;
            pass_votes_power = 0n;
            total_voting_power = Tezos.get_total_voting_power ()
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
            (match get_proposal_winner voting_context period_index config with
                | Some proposal_winner -> 
                    {
                        voting_context = init_new_promotion_voting_period voting_context period_index proposal_winner;
                        finished_voting = None;
                    }
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
        if Set.mem voter proposal.voters
            then acc + 1n
            else acc in
    let upvotes_count = Map.fold get_upvotes_count proposals 0n in
    if upvotes_count < config.upvoting_limit
        then unit
        else failwith Errors.upvoting_limit_exceeded


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
        (config: Storage.config_t)
        : pt Storage.proposal_period_t =
    let _ = assert_upvoting_allowed proposal_period.proposals config proposer in
    let key = get_payload_key payload in
    let _ = match Map.find_opt key proposal_period.proposals with
        | Some _ -> failwith Errors.proposal_already_created
        | None -> unit in
    let value = {
        payload = payload;
        proposer = proposer;
        voters = Set.literal [proposer];
        upvotes_power = voting_power;
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
        (config: Storage.config_t)
        : pt Storage.proposal_period_t =
    let _ = assert_upvoting_allowed proposal_period.proposals config voter in
    let key = get_payload_key payload in
    let proposal_opt = Map.find_opt key proposal_period.proposals in
    let proposal = Option.unopt_with_error proposal_opt Errors.proposal_not_found in
    let _ = if Set.mem voter proposal.voters
        then failwith Errors.proposal_already_upvoted
        else unit in
    let updated_proposal = { 
        proposal with
        voters = Set.add voter proposal.voters;
        upvotes_power = proposal.upvotes_power + voting_power;  
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
    let _ = if Set.mem voter promotion_period.voters
        then failwith Errors.promotion_already_voted
        else unit in
    let updated_promotion = match vote with
        | Yay  -> { promotion_period with yay_votes_power = promotion_period.yay_votes_power + voting_power }
        | Nay  -> { promotion_period with nay_votes_power = promotion_period.nay_votes_power + voting_power }
        | Pass -> { promotion_period with pass_votes_power = promotion_period.pass_votes_power + voting_power } in
    { 
        updated_promotion with 
        voters = Set.add voter promotion_period.voters;
    }
