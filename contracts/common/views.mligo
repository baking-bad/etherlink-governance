#import "storage.mligo" "Storage"
#import "events.mligo" "Events"
#import "voting.mligo" "Voting"

type 'pt proposal_period_t = {
    max_upvotes_voting_power : nat option;
    winner_candidate : 'pt option;
    total_voting_power : nat;
}

type promotion_period_t = {
    yay_voting_power : nat;
    nay_voting_power : nat;
    pass_voting_power : nat;
    total_voting_power : nat;
}

type 'pt voting_context_t = {
    period_index : nat;
    period_type : Storage.period_type_t;
    proposal_period : 'pt proposal_period_t;
    promotion_period : promotion_period_t option;
    last_winner_payload : 'pt option;
}

type 'pt voting_state_t = {
    voting_context : 'pt voting_context_t;
    finished_voting : 'pt Events.voting_finished_event_payload_t option;
}

let get_voting_state
        (type pt)
        (storage : pt Storage.t)
        : pt voting_state_t = 
    //TODO: implement optimization
    let voting_state = Voting.get_voting_state storage in
    let voting_context = voting_state.voting_context in
    let proposal_period = voting_context.proposal_period in
    let promotion_period = match voting_context.promotion_period with
        | Some promotion_period -> 
            Some {
                yay_voting_power = promotion_period.yay_voting_power;
                nay_voting_power = promotion_period.nay_voting_power;
                pass_voting_power = promotion_period.pass_voting_power;
                total_voting_power = promotion_period.total_voting_power;
            } 
        | None -> None in
    {
        voting_context = {
            period_index = voting_context.period_index;
            period_type = voting_context.period_type;
            proposal_period = {
                max_upvotes_voting_power = proposal_period.max_upvotes_voting_power;
                winner_candidate = proposal_period.winner_candidate;
                total_voting_power = proposal_period.total_voting_power;
            };
            promotion_period = promotion_period;
            last_winner_payload =  voting_context.last_winner_payload;
        };
        finished_voting = voting_state.finished_voting
    }