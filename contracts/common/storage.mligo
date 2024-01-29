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
(*
    'pt - payload type. for kernel governance it is bytes, for committee governance it is address set
*)
type 'pt proposal_t = {
    payload : 'pt;
    url : string;
    proposer : address;
    voters: address set;
    up_votes_power: nat;
}

type 'pt proposals_t = (bytes, ('pt proposal_t)) map

type 'pt promotion_t = {
    proposal_payload : 'pt;
    voters : address set;
    yay_vote_power : nat;
    nay_vote_power : nat;
    pass_vote_power : nat;
}

type period_type_t = Proposal | Promotion

type 'pt voting_context_t = {
    period_index : nat;
    period_type : period_type_t;
    proposals : 'pt proposals_t;
    promotion : 'pt promotion_t option;  
    last_winner_payload : 'pt option; // think about naming
}

type 'pt t = {
    config : config_t;
    voting_context : 'pt voting_context_t;
    metadata : (string, bytes) big_map;
}

type promotion_vote_t = Yay | Nay | Pass