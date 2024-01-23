#import "storage.mligo" "Storage"
#import "errors.mligo" "Errors"

// TODO: check division operations

let get_phase_index
        (config : Storage.config_t)
        : nat =
    let blocks_after_start_int = Tezos.get_level () - config.started_at_block in
    match is_nat blocks_after_start_int with // TODO: move to helper func
        | Some blocks_after_start ->  blocks_after_start / config.phase_length
        | None -> failwith Errors.current_level_is_less_than_start_block

let get_min_winning_propsal_voting_power
        (config : Storage.config_t)
        : nat =
    (Tezos.get_total_voting_power () * config.min_proposal_quorum / Storage.ratio_denominator)

let get_proposal_winner
        (proposals : Storage.proposals_t)
        (config : Storage.config_t)
        : bytes option =
    let get_winners = fun ((winner, max_power), (_, proposal) : (bytes option * nat) * (bytes * Storage.proposal_t)) -> 
        if proposal.up_votes_power > max_power
            then (Some(proposal.hash), proposal.up_votes_power)
            else if proposal.up_votes_power = max_power
                then (None, max_power)
                else (winner, max_power) in
    let (winner_hash, winner_up_votes_power) = Map.fold get_winners proposals (None, 0n) in
    if winner_up_votes_power >= (get_min_winning_propsal_voting_power config)
        then winner_hash
        else None

let get_promotion_winner
        (promotion : Storage.promotion_t)
        (config : Storage.config_t)
        : bytes option =
    let { yay_vote_power; nay_vote_power; pass_vote_power; proposal_hash; voters = _; } = promotion in 
    let yay_votes_ratio = yay_vote_power / (yay_vote_power + nay_vote_power) in
    let partisipation_ratio = (yay_vote_power + nay_vote_power + pass_vote_power) / Tezos.get_total_voting_power () in
    let quorum = config.quorum / Storage.ratio_denominator in
    let super_majority = config.super_majority / Storage.ratio_denominator in
    if yay_votes_ratio > quorum && partisipation_ratio > super_majority
        then Some proposal_hash
        else None

let init_new_poposal_voting_contex
        (voting_context : Storage.voting_context_t)
        (phase_index : nat)
        : Storage.voting_context_t =
    { 
        voting_context with 
        phase_index = phase_index;
        phase_type = Proposal;
        proposals = Map.empty;
        promotion = None
    }   

let init_new_promotion_voting_contex
        (voting_context : Storage.voting_context_t)
        (phase_index : nat)
        (proposal_winner : bytes)
        : Storage.voting_context_t =
    { 
        voting_context with 
        phase_index = phase_index;
        phase_type = Promotion;
        promotion = Some {
            proposal_hash = proposal_winner;
            voters = Set.empty;
            yay_vote_power = 0n;
            nay_vote_power = 0n;
            pass_vote_power = 0n;   
        }
    }   

let init_new_voting_context
        (storage : Storage.t)
        (phase_index : nat)
        : Storage.voting_context_t =
    let { voting_context; config; metadata = _} = storage in
    match storage.voting_context.phase_type with
        | Proposal -> 
            (match get_proposal_winner voting_context.proposals config with
                | Some proposal_winner -> init_new_promotion_voting_contex voting_context phase_index proposal_winner
                | None -> init_new_poposal_voting_contex voting_context phase_index)
        | Promotion ->
            let new_proposal_voting_context = init_new_poposal_voting_contex voting_context phase_index in
            (match get_promotion_winner (Option.unopt voting_context.promotion) config with
                | Some promotion_winner -> 
                    { 
                        new_proposal_voting_context with 
                        last_winner_hash = Some promotion_winner
                    } 
                | None -> new_proposal_voting_context)

let get_voting_context 
        (storage : Storage.t)
        : Storage.voting_context_t = 
    let phase_index = get_phase_index storage.config in
    let context = if phase_index = storage.voting_context.phase_index 
        then storage.voting_context 
        else init_new_voting_context storage phase_index in
    context

let assert_current_phase_proposal 
        (voting_context : Storage.voting_context_t)
        : unit =
    match voting_context.phase_type with 
        | Proposal -> unit
        | Promotion -> failwith Errors.not_proposal_phase

let assert_current_phase_promotion 
        (voting_context : Storage.voting_context_t)
        : unit =
    match voting_context.phase_type with
        | Promotion -> unit
        | Proposal -> failwith Errors.not_promotion_phase

let assert_new_proposal_allowed
        (proposals : Storage.proposals_t)
        (config : Storage.config_t)
        (proposer : address)
        : unit =
    let get_proposals_count = fun (acc, (_, proposal) : nat * (bytes * Storage.proposal_t)) ->
        if proposal.proposer = proposer
            then acc + 1n
            else acc in
    let proposals_count = Map.fold get_proposals_count proposals 0n in
    if proposals_count < config.proposals_limit_per_account
        then unit
        else failwith Errors.proposal_limit_exceeded

let add_new_proposal
        (hash : bytes)
        (url : string)
        (proposer : address)
        (voting_power : nat)
        (proposals : Storage.proposals_t)
        : Storage.proposals_t =
    // TODO: ether allow to edit already existent proposal (e.g update url) or disable adding the same proposal twise
    let _ = match Map.find_opt hash proposals with
        | Some _ -> failwith Errors.proposal_already_created
        | None -> unit in
    let value = {
        hash = hash;
        url = url;
        proposer = proposer;
        voters = Set.literal [proposer];
        up_votes_power = voting_power;
    } in
    Map.add hash value proposals

let upvote_proposal
        (hash : bytes)
        (voter : address)
        (voting_power : nat)
        (proposals : Storage.proposals_t)
        : Storage.proposals_t =
    let proposal_opt = Map.find_opt hash proposals in
    let proposal = Option.unopt_with_error proposal_opt Errors.proposal_not_found in
    let _ = if Set.mem voter proposal.voters
        then failwith Errors.proposal_already_upvoted
        else unit in
    let updated_proposal = { 
        proposal with
        voters = Set.add voter proposal.voters;
        up_votes_power = proposal.up_votes_power + voting_power;  
    } in
    Map.update hash (Some updated_proposal) proposals

let vote_promotion
        (vote : Storage.promotion_vote_t)
        (voter : address)
        (voting_power : nat)
        (promotion : Storage.promotion_t)
        : Storage.promotion_t =
    let _ = if Set.mem voter promotion.voters
        then failwith Errors.promotion_already_voted
        else unit in
    let updated_promotion = match vote with
        | Yay  -> { promotion with yay_vote_power = promotion.yay_vote_power + voting_power }
        | Nay  -> { promotion with nay_vote_power = promotion.nay_vote_power + voting_power }
        | Pass -> { promotion with pass_vote_power = promotion.pass_vote_power + voting_power } in
    { 
        updated_promotion with 
        voters = Set.add voter promotion.voters;
    }