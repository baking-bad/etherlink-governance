(*
    NOTE:
    started_at_level and period_length values should be chosen carefully 
    to be sure that the contract governance periods 
    never cross the boundaries of the tezos protocol governance periods. 
    This ensures the immutability of voting power throughout the entire voting period 
*)
type config_t = {
    (* 
        Used to align voting periods with protocol governance periods. 
        Should be the start level of the current protocol governance period 
    *)
    started_at_level : nat;

    (* 
        The duration of the of proposal and promotion periods represented in blocks. 
        period_length = tezos_governance_period_length / N, where N is integer divisor (factor)
    *)
    period_length : nat;

    (* Number of proposals that an account may upvote and submit *)
    upvoting_limit : nat;               

    (* Accounts that can submit new proposals (if set is empty then anyone is allowed) *)
    allowed_proposers : address set;

    (* 
        The scale for proposal_quorum, promotion_quorum and promotion_supermajority params. 
        For example if config.scale = 100 and config.proposal_quorum = 80 
        then proposal_quorum_% == 80 / 100 == .80 == 80%
    *)
    scale : nat;       

    (* 
        Minimum ratio of all the cumulated stake of a proposal upvotes to the total stake 
        to advance the proposal to promotion period 
    *)
    proposal_quorum : nat;     

    (* 
        Minimum ratio of all the cumulated stake of cast ballots (yay, nay, and pass ballots) 
        to the total stake to consider the proposal as a voting winner 
    *)
    promotion_quorum : nat;    

    (* 
        Minimum ratio of cumulated stake of Yay ballots to the cumulated stake 
        of Yay and Nay ballots to consider the proposal as a voting winner
    *)
    promotion_supermajority : nat;      
}

(*
    'pt - payload type. for kernel governance it is bytes, for committee governance it is address set
*)
type 'pt proposal_t = {
    payload : 'pt;
    proposer : address;
    votes : (address, nat) map;
}

type 'pt proposals_t = (bytes, ('pt proposal_t)) map

type 'pt proposal_period_t = {
    proposals : 'pt proposals_t;
    total_voting_power : nat;
}

type promotion_vote_params_t = {
    vote: string;
    voting_power: nat;
}

type 'pt promotion_period_t = {
    payload : 'pt;
    votes : (address, promotion_vote_params_t) map;
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
