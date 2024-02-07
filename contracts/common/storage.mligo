(*
    proposal_quorum, promotion_quorum and promotion_super_majority are represented with scale. 
    For example if scale = 100 and proposal_quorum = 80 then proposal_quorum == .80 == 80%
*)
type config_t = {
    started_at_level : nat;             // used to align with protocol governance cycles
    period_length : nat;                // represented in blocks
    upvoting_limit : nat;               // number of proposals that an account may upvote 
    scale : nat;
    proposal_quorum : nat;
    promotion_quorum : nat;
    promotion_super_majority : nat;
}
(*
    'pt - payload type. for kernel governance it is bytes, for committee governance it is address set
*)
type 'pt proposal_t = {
    payload : 'pt;
    proposer : address;
    voters : address set;
    upvotes_power : nat;
}

type 'pt proposals_t = (bytes, ('pt proposal_t)) map

type 'pt proposal_period_t = {
    proposals : 'pt proposals_t;
    total_voting_power : nat;
}

type 'pt promotion_period_t = {
    payload : 'pt;
    voters : address set;
    yay_votes_power : nat;
    nay_votes_power : nat;
    pass_votes_power : nat;
    total_voting_power : nat;
}

type period_type_t = Proposal | Promotion

type 'pt voting_context_t = {
    period_index : nat;
    period_type : period_type_t;
    proposal_period : 'pt proposal_period_t;
    promotion_period : 'pt promotion_period_t option;
    last_winner_payload : 'pt option;
}

type 'pt t = {
    config : config_t;
    voting_context : ('pt voting_context_t) option;
    metadata : (string, bytes) big_map;
}

type promotion_vote_t = Yay | Nay | Pass
