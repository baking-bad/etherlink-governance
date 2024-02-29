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

    (* 
        The duration of the l2 cooldown period counted in seconds. 
        Used to generate an upgrade payload with activation timestamp 
        on trigger_upgrade entrypoint call 
    *)
    cooldown_period_sec : int;

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
    upvotes_voting_power : nat;
}

type 'pt proposals_t = (bytes, ('pt proposal_t)) big_map

type payload_key_t = bytes

type upvoters_upvotes_count_t = (address, nat) big_map
type upvoters_proposals_t = (address * payload_key_t, unit) big_map

type 'pt proposal_period_t = {
    upvoters_upvotes_count : upvoters_upvotes_count_t;
    upvoters_proposals : upvoters_proposals_t;
    proposals : 'pt proposals_t;
    max_upvotes_voting_power : nat option;
    winner_candidate : 'pt option;
    total_voting_power : nat;
}

type promotion_period_t = {
    voters : (address, unit) big_map;
    yay_voting_power : nat;
    nay_voting_power : nat;
    pass_voting_power : nat;
    total_voting_power : nat;
}

type period_type_t = Proposal | Promotion

type 'pt voting_context_t = {
    period_index : nat;
    period_type : period_type_t;
    proposal_period : 'pt proposal_period_t;
    promotion_period : promotion_period_t option;
    last_winner_payload : 'pt option;
    last_winner_trigger_history : (address, unit) big_map;
}

type 'pt t = {
    config : config_t;
    voting_context : ('pt voting_context_t) option;
    metadata : (string, bytes) big_map;
}
