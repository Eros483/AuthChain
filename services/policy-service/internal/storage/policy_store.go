package storage

import (
	"encoding/json"
	"errors"
	"sync"
)

type DirectoryOwnership struct {
	Directory  string   `json:"directory"`
	Developers []string `json:"developers"`
}

type PolicyStore struct {
	mu              sync.RWMutex
	DirectoryOwners []DirectoryOwnership `json:"directory_owners"`
	LineThreshold   int                  `json:"line_threshold"`
}

func NewPolicyStore() *PolicyStore {
	return &PolicyStore{
		DirectoryOwners: []DirectoryOwnership{},
		LineThreshold:   50,
	}
}

func (ps *PolicyStore) AddDirectoryOwnership(ownership DirectoryOwnership) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if ownership.Directory == "" {
		return errors.New("dir path cannot be empty")
	}

	if len(ownership.Developers) == 0 {
		return errors.New("assign at least 1 dev")
	}

	for i, existing := range ps.DirectoryOwners {
		if existing.Directory == ownership.Directory {
			ps.DirectoryOwners[i] = ownership
			return nil
		}
	}

	ps.DirectoryOwners = append(ps.DirectoryOwners, ownership)
	return nil
}

func (ps *PolicyStore) RemoveDirectoryOwnership(directory string) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	for i, owner := range ps.DirectoryOwners {
		if owner.Directory == directory {
			ps.DirectoryOwners = append(ps.DirectoryOwners[:i], ps.DirectoryOwners[i+1:]...)
			return nil
		}
	}
	return errors.New("dir not found")
}

func (ps *PolicyStore) GetAllOwnership() []DirectoryOwnership {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	result := make([]DirectoryOwnership, len(ps.DirectoryOwners))
	copy(result, ps.DirectoryOwners)
	return result
}

func (ps *PolicyStore) GetDirOwnership(dir string) (*DirectoryOwnership, error) {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	for _, owner := range ps.DirectoryOwners {
		if owner.Directory == dir {
			return &owner, nil
		}
	}
	return nil, errors.New("dir not found")
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

func (ps *PolicyStore) ToJSON() ([]byte, error) {
	ps.mu.RLock()
	defer ps.mu.RUnlock()
	return json.Marshal(ps)
}

func (ps *PolicyStore) FromJSON(data []byte) error {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return json.Unmarshal(data, ps)
}
