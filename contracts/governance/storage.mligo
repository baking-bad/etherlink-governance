let ratio_denominator = 100n

type config_t = {
    rollup_address : address;
    phase_length : nat;
    proposals_limit_per_account : nat;
    min_proposal_quorum : nat; // MIN_WINNING_STAKE_RATIO
    quorum : nat;
    super_majority : nat;
}

type proposal_t = {
    hash : bytes;
    url : string;
    proposer : address;
    voters: address set;
    up_votes_power: nat;
}

type proposals_t = (bytes, proposal_t) map

type promotion_t = {
    proposal_hash : bytes;
    voters : address set;
    yay_vote_power : nat;
    nay_vote_power : nat;
    pass_vote_power : nat;
}

type voting_context_t = {
    phase_index : nat;
    phase_type : nat;
    proposals : proposals_t;
    promotion : promotion_t option;  
    last_promotion_winner_hash : bytes option; // think about naming
}

type t = {
    config : config_t;
    voting_context : voting_context_t;
    metadata : (string, bytes) big_map;
}