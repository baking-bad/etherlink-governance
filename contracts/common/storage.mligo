(*
    started_at_level and period_length values should be chosen carefully to be sure that the contract governance periods 
    never cross the boundaries of the tezos protocol governance periods. This ensures the immutability of voting power throughout the entire voting period 

    proposal_quorum, promotion_quorum and promotion_supermajority are represented with scale. 
    For example if config.scale = 100 and config.proposal_quorum = 80 then proposal_quorum_% == 80 / 100 == .80 == 80%
*)
type config_t = {
    started_at_level : nat;             // used to align voting periods with protocol governance periods. Should be the start level of the current protocol governance period
    period_length : nat;                // the duration of the of proposal and promotion periods represented in blocks. Should be a divisor of protocol governance period length
    upvoting_limit : nat;               // number of proposals that an account may upvote and submit
    allowed_proposers : address set;    // accounts that can submit new proposals (if set is empty then anyone is allowed)
    scale : nat;                        // denominator for proposal_quorum, promotion_quorum and promotion_supermajority values
    proposal_quorum : nat;              // minimum ratio of all the cumulated stake of a proposal upvotes to the total stake to move the proposal to promotion period 
    promotion_quorum : nat;             // minimum ratio of all the cumulated stake of cast ballots (yay, nay, and pass ballots) to the total stake to consider the proposal as a voting winner
    promotion_supermajority : nat;      // minimum ratio of cumulated stake of Yay ballots to the cumulated stake of Yay and Nay ballots to consider the proposal as a voting winner
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
