package storage

import (
	"errors"
	"sync"
)

type PolicyStore struct {
	mu            sync.RWMutex
	LineThreshold int           `json:"line_threshold"`
	ToolRegistry  *ToolRegistry `json:"-"`
}

func NewPolicyStore() *PolicyStore {
	return &PolicyStore{
		LineThreshold: 50,
		ToolRegistry:  NewToolRegistry(),
	}
}

func (ps *PolicyStore) UpdateLineThreshold(threshold int) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if threshold < 0 {
		return errors.New("threshold must be positive")
	}
	ps.LineThreshold = threshold
	return nil
}
