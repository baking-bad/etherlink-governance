#import "storage.mligo" "Storage"

module Governance = struct 

  [@entry]
  let new_proposal (_ : unit) (storage : Storage.t) : operation list * Storage.t = [], storage
  
  [@entry]
  let upvote_proposal (_ : unit) (storage : Storage.t) : operation list * Storage.t = [], storage
  
  [@entry]
  let vote (_ : unit) (storage : Storage.t) : operation list * Storage.t = [], storage
  
  [@entry]
  let trigger_upgrade (_ : unit) (storage : Storage.t) : operation list * Storage.t = [], storage

end