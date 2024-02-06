#import "storage.mligo" "Storage"

type 'pt new_voting_winner_event_payload_t = {
    started_at_period_index : nat;
    ended_at_period_index : nat;
    proposals : 'pt Storage.proposals_t;
    promotion : 'pt Storage.promotion_t;  
    winner_payload : 'pt;
    total_voting_power : nat;
}

let create_new_voting_winner_event
        (type pt)
        (promotion_period_index : nat)
        (proposals : pt Storage.proposals_t)
        (promotion : pt Storage.promotion_t)  
        (winner_payload : pt)
        : operation = 
    let started_at_period_index = match is_nat (promotion_period_index - 1n) with
        | Some started_index -> started_index
        | None -> 0n in
    let ended_at_period_index = promotion_period_index + 1n in
    let event_payload : pt new_voting_winner_event_payload_t= {
        started_at_period_index = started_at_period_index;
        ended_at_period_index = ended_at_period_index;
        proposals = proposals;
        promotion = promotion;  
        winner_payload = winner_payload;
        total_voting_power = Tezos.get_total_voting_power ();
    } in
    Tezos.emit "%new_voting_winner" event_payload