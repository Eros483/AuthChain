package validator

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"sync"
)

type Validator struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	PublicKey string `json:"public_key"`
	Active    bool   `json:"active"`
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

func (vr *ValidatorRegistry) AddValidator(validator *Validator) error {
	vr.mu.Lock()
	defer vr.mu.Unlock()

	if validator.ID == "" {
		return errors.New("validator ID cannot be empty")
	}

	if _, exists := vr.validators[validator.ID]; exists {
		return fmt.Errorf("validator %s already exists", validator.ID)
	}

	vr.validators[validator.ID] = validator
	return nil
}

func (vr *ValidatorRegistry) RemoveValidator(id string) error {
	vr.mu.Lock()
	defer vr.mu.Unlock()

	validator, exists := vr.validators[id]
	if !exists {
		return fmt.Errorf("validator %s not found", id)
	}

	validator.Active = false
	return nil
}

func (vr *ValidatorRegistry) GetValidator(id string) (*Validator, error) {
	vr.mu.RLock()
	defer vr.mu.RUnlock()

	validator, exists := vr.validators[id]
	if !exists {
		return nil, fmt.Errorf("validator %s not found", id)
	}

	return validator, nil
}

func (vr *ValidatorRegistry) GetActiveValidators() []*Validator {
	vr.mu.RLock()
	defer vr.mu.RUnlock()

	var active []*Validator
	for _, v := range vr.validators {
		if v.Active {
			active = append(active, v)
		}
	}

	return active
}

func (vr *ValidatorRegistry) GetQuorumSize() int {
	active := vr.GetActiveValidators()
	return (len(active) * 2 / 3) + 1
}

func (vr *ValidatorRegistry) ValidateQuorum(validatorIDs []string) error {
	requiredQuorum := vr.GetQuorumSize()

	if len(validatorIDs) < requiredQuorum {
		return fmt.Errorf("insufficient signatures: got %d, need %d", len(validatorIDs), requiredQuorum)
	}

	for _, id := range validatorIDs {
		validator, err := vr.GetValidator(id)
		if err != nil {
			return fmt.Errorf("unknown validator: %s", id)
		}
		if !validator.Active {
			return fmt.Errorf("inactive validator: %s", id)
		}
	}

	return nil
}

func (v *Validator) SignBlock(blockHash string) string {
	data := v.ID + blockHash
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

func (v *Validator) VerifySignature(blockHash, signature string) bool {
	expectedSig := v.SignBlock(blockHash)
	return expectedSig == signature
}
