package consensus

import (
	"errors"
	"sync"
	"time"

	"authchain/internal/block"
	"authchain/internal/validator"
)

type PendingBlock struct {
	Block     *block.Block
	Approvals int
	CreatedAt time.Time
}

type QuorumConsensus struct {
	mu                sync.RWMutex
	pendingBlocks     map[string]*PendingBlock
	validatorRegistry *validator.ValidatorRegistry
	timeout           time.Duration
}

func NewQuorumConsensus(registry *validator.ValidatorRegistry) *QuorumConsensus {
	qc := &QuorumConsensus{
		pendingBlocks:     make(map[string]*PendingBlock),
		validatorRegistry: registry,
		timeout:           5 * time.Minute,
	}
	go qc.cleanup()
	return qc
}

func (qc *QuorumConsensus) ProposeBlock(b *block.Block) {
	qc.mu.Lock()
	defer qc.mu.Unlock()

	qc.pendingBlocks[b.Hash] = &PendingBlock{
		Block:     b,
		Approvals: 0,
		CreatedAt: time.Now(),
	}
}

func (qc *QuorumConsensus) Approve(blockHash string) error {
	qc.mu.Lock()
	defer qc.mu.Unlock()

	pb, ok := qc.pendingBlocks[blockHash]
	if !ok {
		return errors.New("block not pending")
	}

	pb.Approvals++
	return nil
}

func (qc *QuorumConsensus) HasQuorum(blockHash string) bool {
	qc.mu.RLock()
	defer qc.mu.RUnlock()

	pb, ok := qc.pendingBlocks[blockHash]
	if !ok {
		return false
	}

	required := qc.validatorRegistry.GetQuorumSize()
	return pb.Approvals >= required
}

func (qc *QuorumConsensus) Remove(blockHash string) {
	qc.mu.Lock()
	defer qc.mu.Unlock()
	delete(qc.pendingBlocks, blockHash)
}

func (qc *QuorumConsensus) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	for range ticker.C {
		qc.mu.Lock()
		now := time.Now()
		for h, pb := range qc.pendingBlocks {
			if now.Sub(pb.CreatedAt) > qc.timeout {
				delete(qc.pendingBlocks, h)
			}
		}
		qc.mu.Unlock()
	}
}
