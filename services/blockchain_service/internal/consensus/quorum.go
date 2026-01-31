package consensus

import (
	"authchain/internal/block"
	"authchain/internal/validator"
	"errors"
	"fmt"
	"sync"
	"time"
)

type PendingBlock struct {
	Block      *block.Block
	Signatures map[string]block.Signature
	CreatedAt  time.Time
}

type QuorumConsensus struct {
	mu                sync.RWMutex
	pendingBlocks     map[string]*PendingBlock
	validatorRegistry *validator.ValidatorRegistry
	consensusTimeout  time.Duration
}

func NewQuorumConsensus(registry *validator.ValidatorRegistry) *QuorumConsensus {
	qc := &QuorumConsensus{
		pendingBlocks:     make(map[string]*PendingBlock),
		validatorRegistry: registry,
		consensusTimeout:  5 * time.Minute,
	}

	go qc.cleanupExpiredBlocks()

	return qc
}

func (qc *QuorumConsensus) ProposeBlock(b *block.Block) error {
	qc.mu.Lock()
	defer qc.mu.Unlock()

	if _, exists := qc.pendingBlocks[b.Hash]; exists {
		return errors.New("block already pending")
	}

	qc.pendingBlocks[b.Hash] = &PendingBlock{
		Block:      b,
		Signatures: make(map[string]block.Signature),
		CreatedAt:  time.Now(),
	}

	return nil
}

func (qc *QuorumConsensus) AddValidatorSignature(blockHash string, sig block.Signature) error {
	qc.mu.Lock()
	defer qc.mu.Unlock()

	pending, exists := qc.pendingBlocks[blockHash]
	if !exists {
		return errors.New("block not found in pending")
	}

	v, err := qc.validatorRegistry.GetValidator(sig.ValidatorID)
	if err != nil {
		return fmt.Errorf("unknown validator: %w", err)
	}

	if !v.Active {
		return fmt.Errorf("validator %s is not active", sig.ValidatorID)
	}

	if !v.VerifySignature(blockHash, sig.Signature) {
		return errors.New("invalid signature")
	}

	pending.Signatures[sig.ValidatorID] = sig
	pending.Block.AddValidSignature(sig)

	return nil
}

func (qc *QuorumConsensus) HasQuorum(blockHash string) (bool, error) {
	qc.mu.RLock()
	defer qc.mu.RUnlock()

	pending, exists := qc.pendingBlocks[blockHash]
	if !exists {
		return false, errors.New("block not found")
	}

	requiredQuorum := qc.validatorRegistry.GetQuorumSize()
	return len(pending.Signatures) >= requiredQuorum, nil
}

func (qc *QuorumConsensus) GetBlock(blockHash string) (*block.Block, error) {
	qc.mu.RLock()
	defer qc.mu.RUnlock()

	pending, exists := qc.pendingBlocks[blockHash]
	if !exists {
		return nil, errors.New("block not found")
	}

	hasQuorum, _ := qc.HasQuorum(blockHash)
	if !hasQuorum {
		return nil, errors.New("block has not reached quorum")
	}

	return pending.Block, nil
}

func (qc *QuorumConsensus) RemovePending(blockHash string) {
	qc.mu.Lock()
	defer qc.mu.Unlock()

	delete(qc.pendingBlocks, blockHash)
}

func (qc *QuorumConsensus) GetPendingBlocks() []*PendingBlock {
	qc.mu.RLock()
	defer qc.mu.RUnlock()

	var pending []*PendingBlock
	for _, pb := range qc.pendingBlocks {
		pending = append(pending, pb)
	}

	return pending
}

func (qc *QuorumConsensus) cleanupExpiredBlocks() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		qc.mu.Lock()
		now := time.Now()
		for hash, pending := range qc.pendingBlocks {
			if now.Sub(pending.CreatedAt) > qc.consensusTimeout {
				delete(qc.pendingBlocks, hash)
			}
		}
		qc.mu.Unlock()
	}
}
