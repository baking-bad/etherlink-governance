#import "common/storage.mligo" "Storage"
#import "common/errors.mligo" "Errors"
#import "common/voting.mligo" "Voting"
#import "common/entrypoints.mligo" "Entrypoints"
#import "common/views.mligo" "Views"

module SecurityGovernanceCommittee = struct

    let max_committee_size = 20n

    type payload_t = address set 
    type storage_t = payload_t Storage.t
    type return_t = operation list * storage_t


    [@entry] 
    let new_proposal 
            (addresses : payload_t)
            (storage : storage_t) 
            : return_t = 
        let _ = assert_with_error (Set.size addresses <= max_committee_size) Errors.incorrect_committee_size in
        Entrypoints.new_proposal addresses storage
  

    [@entry]
    let upvote_proposal 
            (addresses : payload_t)
            (storage : storage_t) 
            : return_t = 
        Entrypoints.upvote_proposal addresses storage
  

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
    let check_address_in_committee
            (address : address) 
            (storage : storage_t) 
            : bool = 
        let voting_state = Voting.get_voting_state storage in
        let last_winner = voting_state.last_winner in
        let last_winner = Option.unopt_with_error last_winner Errors.last_winner_payload_not_found in
        Set.mem address last_winner.payload
end