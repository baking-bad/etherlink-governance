type config_t = {
    rollup_address : address;
    phase_length : nat;
    proposals_limit_per_account : nat;
    min_proposal_quorum : nat; // MIN_WINNING_STAKE_RATIO
    super_majority : nat;
    quorum : nat;
}

type proposal_t = {
    hash : bytes;
    url : string;
    submitter : address;
}

type promotion_t = {
    proposal_hash : bytes;
    voters : address set;
    yay_vote_power : nat;
    no_vote_power : nat;
    pass_vote_power : nat;
}

type voting_context_t = {
    phase_index : nat;
    phase_type : nat;
    proposals : (bytes, proposal_t) map;
    promotion : promotion_t;  
}

type t = {
    config : config_t;
    last_selected_proposal_hash : bytes;
    voting_context : voting_context_t;
    metadata : (string, bytes) big_map;
}