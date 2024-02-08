#import "storage.mligo" "Storage"

type 'pt voting_finished_event_payload_t = {
    finished_at_period_index : nat;
    proposal_period : 'pt Storage.proposal_period_t;
    promotion_period : 'pt Storage.promotion_period_t option;  
    winner_payload : 'pt option;
}

let create_voting_finished_event
        (type pt)
        (voting_context : pt Storage.voting_context_t)  
        (winner_payload : pt option)
        : pt voting_finished_event_payload_t = 
    let event_payload : pt voting_finished_event_payload_t= {
        finished_at_period_index = voting_context.period_index + 1n;
        proposal_period = voting_context.proposal_period;
        promotion_period = voting_context.promotion_period;  
        winner_payload = winner_payload;
    } in
    event_payload

let create_voting_finished_event_operation
        (type pt)
        (event_payload : pt voting_finished_event_payload_t)
        : operation =
    Tezos.emit "%voting_finished" event_payload
