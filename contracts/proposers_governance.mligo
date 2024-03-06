#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/voting.mligo" "Voting"
#import "common/entrypoints.mligo" "Entrypoints"
#import "common/views.mligo" "Views"

module ProposersCommitteeGovernance = struct
    (*
        This contract serves as a supplementary contract for other governance contracts. 
        The contract includes, as a payload, the key hash set of allowed proposers for the main governance contract, 
        which in turn utilizes the check_key_hash_in_last_winner view of this contract to verify allowed proposers.
    *)
    let max_key_hash_set_size = 20n

    type payload_t = key_hash set 
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t


    [@entry] 
    let new_proposal 
            (key_hash_set : payload_t)
            (storage : storage_t) 
            : return_t = 
        let _ = assert_with_error (Set.size key_hash_set <= max_key_hash_set_size) Errors.incorrect_key_hash_set_size in
        Entrypoints.new_proposal key_hash_set storage
  

    [@entry]
    let upvote_proposal 
            (key_hash_set : payload_t)
            (storage : storage_t) 
            : return_t = 
        Entrypoints.upvote_proposal key_hash_set storage
  

    [@entry]
    let vote 
            (vote : string) 
            (storage : storage_t) 
            : return_t =
        Entrypoints.vote vote storage
  

    [@view] 
    let get_voting_state
            (_ : unit) 
            (storage : storage_t) 
            : payload_t Views.voting_state_t = 
        Views.get_voting_state storage


    [@view] 
    let check_key_hash_in_last_winner
            (key_hash : key_hash) 
            (storage : storage_t) 
            : bool = 
        let voting_state = Voting.get_voting_state storage in
        let last_winner = Option.unopt_with_error voting_state.last_winner Errors.last_winner_not_found in
        Set.mem key_hash last_winner.payload
end