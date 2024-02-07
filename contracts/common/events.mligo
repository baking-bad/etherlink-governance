#import "storage.mligo" "Storage"

type 'pt new_voting_winner_event_payload_t = {
    started_at_period_index : nat;
    ended_at_period_index : nat;
    proposal_period : 'pt Storage.proposal_period_t;
    promotion_period : 'pt Storage.promotion_period_t;  
    winner_payload : 'pt;
}

type 'pt event_t = New_voting_winner of 'pt new_voting_winner_event_payload_t

let create_new_voting_winner_event
        (type pt)
        (promotion_period_index : nat)
        (proposal_period : pt Storage.proposal_period_t)
        (promotion_period : pt Storage.promotion_period_t)  
        (winner_payload : pt)
        : pt event_t = 
    let started_at_period_index = match is_nat (promotion_period_index - 1n) with
        | Some started_index -> started_index
        | None -> 0n in
    let ended_at_period_index = promotion_period_index + 1n in
    let event_payload : pt new_voting_winner_event_payload_t= {
        started_at_period_index = started_at_period_index;
        ended_at_period_index = ended_at_period_index;
        proposal_period = proposal_period;
        promotion_period = promotion_period;  
        winner_payload = winner_payload;
    } in
    New_voting_winner event_payload

let map_event_to_operation
        (type pt)
        (event : pt event_t)
        : operation =
    match event with
        | New_voting_winner event_payload -> Tezos.emit "%new_voting_winner" event_payload

let map_events_to_operations
        (type pt)
        (events : (pt event_t) list)
        : operation list =
    List.map map_event_to_operation events