package solana

import (
	"sync"
)

var (
	mu sync.RWMutex

	approvedProposals = map[string]bool{}
	rejectedProposals = map[string]bool{}
)

func IsExecutionApproved(proposalID string) (bool, error) {
	mu.RLock()
	defer mu.RUnlock()

	if rejectedProposals[proposalID] {
		return false, nil
	}

	return approvedProposals[proposalID], nil
}

func MarkApproved(proposalID string) {
	mu.Lock()
	defer mu.Unlock()

	approvedProposals[proposalID] = true
}

func MarkRejected(proposalID string) {
	mu.Lock()
	defer mu.Unlock()

	rejectedProposals[proposalID] = true
}
