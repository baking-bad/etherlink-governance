#import "storage.mligo" "Storage"
#import "events.mligo" "Events"
#import "voting.mligo" "Voting"

type 'pt voting_context_t = {
    period_index : nat;
    period_type : Storage.period_type_t;
    remaining_blocks : nat;
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
    {
        voting_context = {
            period_index = voting_context.period_index;
            period_type = voting_context.period_type;
            remaining_blocks = Voting.get_current_period_remaining_blocks storage.config;
        };
        finished_voting = voting_state.finished_voting
    }