package chain

import (
	"authchain/internal/block"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sync"
)

type Blockchain struct {
	mu     sync.RWMutex
	Blocks []*block.Block `json:"blocks"`
}

func NewBlockchain() *Blockchain {
	return &Blockchain{
		Blocks: []*block.Block{block.GenesisBlock()},
	}
}

func (bc *Blockchain) AddBlock(data block.BlockData) (*block.Block, error) {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	lastBlock := bc.Blocks[len(bc.Blocks)-1]
	newBlock := block.NewBlock(
		lastBlock.Index+1,
		lastBlock.Hash,
		data,
	)

	if err := newBlock.Verify(lastBlock); err != nil {
		return nil, fmt.Errorf("block verification failed: %w", err)
	}

	bc.Blocks = append(bc.Blocks, newBlock)
	return newBlock, nil
}

func (bc *Blockchain) GetLatestBlock() *block.Block {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	return bc.Blocks[len(bc.Blocks)-1]
}

func (bc *Blockchain) GetBlock(index uint64) (*block.Block, error) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	if index >= uint64(len(bc.Blocks)) {
		return nil, errors.New("block not found")
	}

	return bc.Blocks[index], nil
}

func (bc *Blockchain) GetBlockByHash(hash string) (*block.Block, error) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	for _, b := range bc.Blocks {
		if b.Hash == hash {
			return b, nil
		}
	}

	return nil, errors.New("block not found")
}

func (bc *Blockchain) FindByProposalID(proposalID string) ([]*block.Block, error) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	var results []*block.Block
	for _, b := range bc.Blocks {
		if b.Data.ProposalID == proposalID {
			results = append(results, b)
		}
	}

	if len(results) == 0 {
		return nil, errors.New("no blocks found for proposal")
	}

	return results, nil
}

func (bc *Blockchain) Verify() error {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	for i := 1; i < len(bc.Blocks); i++ {
		currentBlock := bc.Blocks[i]
		previousBlock := bc.Blocks[i-1]

		if err := currentBlock.Verify(previousBlock); err != nil {
			return fmt.Errorf("block %d verification failed: %w", i, err)
		}
	}

	return nil
}

func (bc *Blockchain) Length() int {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	return len(bc.Blocks)
}

func (bc *Blockchain) SaveToFile(filepath string) error {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	data, err := json.MarshalIndent(bc, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal blockchain: %w", err)
	}

	return os.WriteFile(filepath, data, 0644)
}

func LoadFromFile(filepath string) (*Blockchain, error) {
	if _, err := os.Stat(filepath); os.IsNotExist(err) {
		return NewBlockchain(), nil
	}

	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var bc Blockchain
	if err := json.Unmarshal(data, &bc); err != nil {
		return nil, fmt.Errorf("failed to unmarshal blockchain: %w", err)
	}

	if err := bc.Verify(); err != nil {
		return nil, fmt.Errorf("loaded blockchain is corrupted: %w", err)
	}

	return &bc, nil
}

func (bc *Blockchain) GetChainHash() string {
	return bc.GetLatestBlock().Hash
}
