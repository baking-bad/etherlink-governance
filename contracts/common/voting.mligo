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
        (proposals : pt Storage.proposals_t)
        (config : Storage.config_t)
        : pt option =
    let get_winners = fun ((winner, max_power), (_, proposal) : (pt option * nat) * (bytes * pt Storage.proposal_t)) -> 
        if proposal.upvotes_power > max_power
            then (Some(proposal.payload), proposal.upvotes_power)
            else if proposal.upvotes_power = max_power
                then (None, max_power)
                else (winner, max_power) in
    let (winner_payload, winner_upvotes_power) = Map.fold get_winners proposals (None, 0n) in
    let proposal_quorum_reached = winner_upvotes_power * Storage.scale >= Tezos.get_total_voting_power () * config.proposal_quorum in
    if proposal_quorum_reached
        then winner_payload
        else None


let get_promotion_winner
        (type pt)
        (promotion : pt Storage.promotion_t)
        (config : Storage.config_t)
        : pt option =
    let { yay_votes_power; nay_votes_power; pass_votes_power; proposal_payload; voters = _; } = promotion in 
    let quorum_reached = (yay_votes_power + nay_votes_power + pass_votes_power) * Storage.scale / Tezos.get_total_voting_power () >= config.promotion_quorum in
    let yay_nay_votes_sum = yay_votes_power + nay_votes_power in
    let super_majority_reached = if yay_nay_votes_sum > 0n
        then yay_votes_power * Storage.scale / yay_nay_votes_sum >= config.promotion_super_majority
        else false in
    if quorum_reached && super_majority_reached 
        then Some proposal_payload
        else None


let init_new_poposal_voting_contex
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (period_index : nat)
        : pt Storage.voting_context_t =
    { 
        voting_context with 
        period_index = period_index;
        period_type = Proposal;
        proposals = Map.empty;
        promotion = None
    }   


let init_new_promotion_voting_contex
        (type pt)
        (voting_context : pt Storage.voting_context_t)
        (period_index : nat)
        (proposal_winner : pt)
        : pt Storage.voting_context_t =
    { 
        voting_context with 
        period_index = period_index;
        period_type = Promotion;
        promotion = Some {
            proposal_payload = proposal_winner;
            voters = Set.empty;
            yay_votes_power = 0n;
            nay_votes_power = 0n;
            pass_votes_power = 0n;   
        }
    }   


type 'pt voting_context_with_events_t = {
    voting_context : 'pt Storage.voting_context_t;
    events : operation list;
}

let init_new_voting_context
        (type pt)
        (storage : pt Storage.t)
        (period_index : nat)
        : pt voting_context_with_events_t =
    let { voting_context; config; metadata = _} = storage in
    match storage.voting_context.period_type with
        | Proposal -> 
            if period_index = voting_context.period_index + 1n
                then (match get_proposal_winner voting_context.proposals config with
                    | Some proposal_winner -> 
                        {
                            voting_context = init_new_promotion_voting_contex voting_context period_index proposal_winner;
                            events = [];
                        }
                    | None -> 
                        {
                            voting_context = init_new_poposal_voting_contex voting_context period_index;
                            events = [];
                        })
                else 
                    {
                        voting_context = init_new_poposal_voting_contex voting_context period_index;
                        events = [];
                    }
        | Promotion ->
            let new_proposal_voting_context = init_new_poposal_voting_contex voting_context period_index in
            let promotion = Option.unopt voting_context.promotion in
            (match get_promotion_winner promotion config with
                | Some promotion_winner ->
                    let new_proposal_voting_context_with_new_winner = { 
                        new_proposal_voting_context with 
                        last_winner_payload = Some promotion_winner
                    } in
                    let new_voting_winner_event = Events.create_new_voting_winner_event voting_context.period_index voting_context.proposals promotion promotion_winner in
                    { 
                        voting_context = new_proposal_voting_context_with_new_winner;
                        events = [new_voting_winner_event];
                    }
                | None -> 
                    {
                        voting_context = new_proposal_voting_context;
                        events = [];
                    })


let get_voting_context
        (type pt)
        (storage : pt Storage.t)
        : pt voting_context_with_events_t = 
    let period_index = get_period_index storage.config in
    let context = if period_index = storage.voting_context.period_index 
        then {
            voting_context = storage.voting_context;
            events = []
        } 
        else init_new_voting_context storage period_index in
    context


type 'pt extended_voting_context_t = {
    voting_context : 'pt Storage.voting_context_t;
    total_voting_power : nat;
}

let get_extended_voting_context
        (type pt)
        (storage : pt Storage.t) 
        : pt extended_voting_context_t = 
    let {voting_context; events=_} = get_voting_context storage in
    { 
        voting_context = voting_context;
        total_voting_power = Tezos.get_total_voting_power ();
    }


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
    let votings_count = Map.fold get_upvotes_count proposals 0n in
    if votings_count < config.upvoting_limit
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
        (proposals : pt Storage.proposals_t)
        (config: Storage.config_t)
        : pt Storage.proposals_t =
    let _ = assert_upvoting_allowed proposals config proposer in
    let key = get_payload_key payload in
    let _ = match Map.find_opt key proposals with
        | Some _ -> failwith Errors.proposal_already_created
        | None -> unit in
    let value = {
        payload = payload;
        proposer = proposer;
        voters = Set.literal [proposer];
        upvotes_power = voting_power;
    } in
    Map.add key value proposals


let upvote_proposal
        (type pt)
        (payload : pt)
        (voter : address)
        (voting_power : nat)
        (proposals : pt Storage.proposals_t)
        (config: Storage.config_t)
        : pt Storage.proposals_t =
    let _ = assert_upvoting_allowed proposals config voter in
    let key = get_payload_key payload in
    let proposal_opt = Map.find_opt key proposals in
    let proposal = Option.unopt_with_error proposal_opt Errors.proposal_not_found in
    let _ = if Set.mem voter proposal.voters
        then failwith Errors.proposal_already_upvoted
        else unit in
    let updated_proposal = { 
        proposal with
        voters = Set.add voter proposal.voters;
        upvotes_power = proposal.upvotes_power + voting_power;  
    } in
    Map.update key (Some updated_proposal) proposals


let vote_promotion
        (type pt)
        (vote : Storage.promotion_vote_t)
        (voter : address)
        (voting_power : nat)
        (promotion : pt Storage.promotion_t)
        : pt Storage.promotion_t =
    let _ = if Set.mem voter promotion.voters
        then failwith Errors.promotion_already_voted
        else unit in
    let updated_promotion = match vote with
        | Yay  -> { promotion with yay_votes_power = promotion.yay_votes_power + voting_power }
        | Nay  -> { promotion with nay_votes_power = promotion.nay_votes_power + voting_power }
        | Pass -> { promotion with pass_votes_power = promotion.pass_votes_power + voting_power } in
    { 
        updated_promotion with 
        voters = Set.add voter promotion.voters;
    }
