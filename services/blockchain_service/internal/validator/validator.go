package validator

import (
	"errors"
	"sync"
)

type Validator struct {
	Wallet string `json:"wallet"` // Solana wallet
	Name   string `json:"name"`
	Active bool   `json:"active"`
}

type ValidatorRegistry struct {
	mu         sync.RWMutex
	validators map[string]*Validator
}

func NewValidatorRegistry() *ValidatorRegistry {
	return &ValidatorRegistry{
		validators: make(map[string]*Validator),
	}
}

func (vr *ValidatorRegistry) AddValidator(v *Validator) error {
	vr.mu.Lock()
	defer vr.mu.Unlock()

	if v.Wallet == "" {
		return errors.New("wallet cannot be empty")
	}

	if _, exists := vr.validators[v.Wallet]; exists {
		return errors.New("validator already exists")
	}

	v.Active = true
	vr.validators[v.Wallet] = v
	return nil
}

func (vr *ValidatorRegistry) RemoveValidator(wallet string) error {
	vr.mu.Lock()
	defer vr.mu.Unlock()

	v, ok := vr.validators[wallet]
	if !ok {
		return errors.New("validator not found")
	}

	v.Active = false
	return nil
}

func (vr *ValidatorRegistry) GetActiveValidators() []*Validator {
	vr.mu.RLock()
	defer vr.mu.RUnlock()

	var out []*Validator
	for _, v := range vr.validators {
		if v.Active {
			out = append(out, v)
		}
	}
	return out
}

func (vr *ValidatorRegistry) GetQuorumSize() int {
	active := len(vr.GetActiveValidators())
	return (active * 2 / 3) + 1
}
