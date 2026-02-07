package governance

import (
	"errors"
	"sync"
	"time"
)

type Proposal struct {
	ProposalID       string
	CheckpointID     string
	ToolName         string
	ToolArguments    map[string]interface{}
	ReasoningSummary string
	Status           string
	DecisionBy       string
	CreatedAt        time.Time
	ResolvedAt       *time.Time
}

type ProposalStore struct {
	mu        sync.RWMutex
	proposals map[string]*Proposal
}

func NewProposalStore() *ProposalStore {
	return &ProposalStore{
		proposals: make(map[string]*Proposal),
	}
}

func (ps *ProposalStore) Store(p *Proposal) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if _, exists := ps.proposals[p.ProposalID]; exists {
		return errors.New("proposal exists")
	}

	ps.proposals[p.ProposalID] = p
	return nil
}

func (ps *ProposalStore) Get(id string) (*Proposal, error) {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	p, ok := ps.proposals[id]
	if !ok {
		return nil, errors.New("proposal not found")
	}
	return p, nil
}

func (ps *ProposalStore) Resolve(id string, approved bool, decisionBy string) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	p, ok := ps.proposals[id]
	if !ok {
		return errors.New("proposal not found")
	}

	now := time.Now()
	p.ResolvedAt = &now
	p.DecisionBy = decisionBy

	if approved {
		p.Status = "approved"
	} else {
		p.Status = "rejected"
	}

	return nil
}
