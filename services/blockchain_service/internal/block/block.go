package block

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"time"
)

type Block struct {
	Index        uint64      `json:"index"`
	Timestamp    int64       `json:"timestamp"`
	PreviousHash string      `json:"previous_hash"`
	Hash         string      `json:"hash"`
	Data         BlockData   `json:"data"`
	ValidatorSig []Signature `json:"validator_sig"`
}

type BlockData struct {
	ProposalID       string                 `json:"proposal_id"`
	CheckpointID     string                 `json:"checkpoint_id"`
	ToolName         string                 `json:"tool_name"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Decision         Decision               `json:"decision"`
	Timestamp        int64                  `json:"timestamp"`
}

type Decision struct {
	Approved        bool   `json:"approved"`
	DecisionBy      string `json:"decision_by"`
	RejectionReason string `json:"rejiction_reason,omitempty"`
	Timestamp       int64  `json:"timestamp"`
}

type Signature struct {
	ValidatorID   string `json:"validator_id"`
	ValidatorName string `json:"validator_name"`
	Signature     string `json:"signature"`
	Tiemstamp     int64  `json:"timestamp"`
}

func NewBlock(index uint64, previousHash string, data BlockData) *Block {
	block := &Block{
		Index:        index,
		Timestamp:    time.Now().Unix(),
		PreviousHash: previousHash,
		Data:         data,
		ValidatorSig: []Signature{},
	}
	block.Hash = block.calculateHash()
	return block
}

func (b *Block) calculateHash() string {
	record := fmt.Sprintf("%d%d%s%s", b.Index, b.Timestamp, b.PreviousHash, b.dataString())

	h := sha256.New()
	h.Write([]byte(record))
	return fmt.Sprintf("%x", h.Sum(nil))
}

func (b *Block) dataString() string {
	data, _ := json.Marshal(b.Data)
	return string(data)
}

func (b *Block) AddValidSignature(sig Signature) {
	b.ValidatorSig = append(b.ValidatorSig, sig)
}

func (b *Block) HasQuorum(reqCount int) bool {
	return len(b.ValidatorSig) >= reqCount
}

func (b *Block) Verify(previousBlock *Block) error {
	if b.Hash != b.calculateHash() {
		return fmt.Errorf("block hash is invalid")
	}

	if b.Index > 0 {
		if previousBlock == nil {
			return fmt.Errorf("missing prev block")
		}
		if b.PreviousHash != previousBlock.Hash {
			return fmt.Errorf("prev hash mismatch")
		}
		if b.Index != previousBlock.Index+1 {
			return fmt.Errorf("idx not sequential")
		}
	}
	return nil
}

func GenesisBlock() *Block {
	genesisData := BlockData{
		ProposalID:       "genesis",
		CheckpointID:     "genesis",
		ToolName:         "init",
		ToolArguments:    map[string]interface{}{},
		ReasoningSummary: "AuthChain Genesis block",
		Decision: Decision{
			Approved:   true,
			DecisionBy: "system",
			Timestamp:  time.Now().Unix(),
		},
		Timestamp: time.Now().Unix(),
	}

	return NewBlock(0, "0", genesisData)
}
