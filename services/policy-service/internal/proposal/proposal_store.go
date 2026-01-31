package proposal

import (
	"errors"
	"policyservice/internal/policy"

	"sync"
	"time"
)

type StoredProposal struct {
	Facts      policy.ProposalFacts  `json:"facts"`
	Result     policy.PriorityResult `json:"result"`
	Status     string                `json:"status"`
	CreatedAt  time.Time             `json:"created_at"`
	ResolvedAt *time.Time            `json:"resolved_at,omitempty"`
}

type ProposalStore struct {
	mu        sync.RWMutex
	proposals map[string]*StoredProposal
}

func NewProposalStore() *ProposalStore {
	return &ProposalStore{
		proposals: make(map[string]*StoredProposal),
	}
}

func (ps *ProposalStore) Store(facts policy.ProposalFacts, result policy.PriorityResult) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if facts.ProposalID == "" {
		return errors.New("proposal_id cannot be empty")
	}

	if _, exists := ps.proposals[facts.ProposalID]; exists {
		return errors.New("proposal already exists")
	}

	ps.proposals[facts.ProposalID] = &StoredProposal{
		Facts:     facts,
		Result:    result,
		Status:    "pending",
		CreatedAt: time.Now(),
	}

	return nil
}

func (ps *ProposalStore) Get(proposalID string) (*StoredProposal, error) {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	proposal, exists := ps.proposals[proposalID]
	if !exists {
		return nil, errors.New("proposal not found")
	}

	return proposal, nil
}

func (ps *ProposalStore) MarkResolved(proposalID string, approved bool) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	proposal, exists := ps.proposals[proposalID]
	if !exists {
		return errors.New("proposal not found")
	}

	if proposal.Status != "pending" {
		return errors.New("proposal already resolved")
	}

	if approved {
		proposal.Status = "approved"
	} else {
		proposal.Status = "rejected"
	}

	now := time.Now()
	proposal.ResolvedAt = &now

	return nil
}

func (ps *ProposalStore) GetPending() []*StoredProposal {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	var pending []*StoredProposal
	for _, proposal := range ps.proposals {
		if proposal.Status == "pending" {
			pending = append(pending, proposal)
		}
	}

	return pending
}

func (ps *ProposalStore) Cleanup(olderThan time.Duration) int {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	removed := 0
	cutoff := time.Now().Add(-olderThan)

	for id, proposal := range ps.proposals {
		if proposal.Status != "pending" && proposal.ResolvedAt != nil && proposal.ResolvedAt.Before(cutoff) {
			delete(ps.proposals, id)
			removed++
		}
	}

	return removed
}

func (ps *ProposalStore) Count() map[string]int {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	counts := map[string]int{
		"pending":  0,
		"approved": 0,
		"rejected": 0,
	}

	for _, proposal := range ps.proposals {
		counts[proposal.Status]++
	}

	return counts
}
