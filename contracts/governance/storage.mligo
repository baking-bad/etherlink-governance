(*
    min_proposal_quorum, quorum and super_majority
    are represented with scale = 100, ex. 80 = .80 = 80%
*)
let scale = 100n
type config_t = {
    started_at_block : nat;             // used to align with protocol governance cycles
    period_length : nat;                // represented in blocks
    proposals_limit_per_account : nat;
    min_proposal_quorum : nat;          // min_winning_stake_ratio
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

type period_type_t = Proposal | Promotion

type voting_context_t = {
    period_index : nat;
    period_type : period_type_t;
    proposals : proposals_t;
    promotion : promotion_t option;  
    last_winner_hash : bytes option; // think about naming
}

type t = {
    config : config_t;
    voting_context : voting_context_t;
    metadata : (string, bytes) big_map;
}

type promotion_vote_t = Yay | Nay | Pass
