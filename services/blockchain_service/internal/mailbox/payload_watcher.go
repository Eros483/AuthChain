package mailbox

import (
	"authchain/internal/block"
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/validator"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"
)

const (
	BlockchainMailbox = "../../services/ipc_mailbox/blockchain"
)

type PayloadWatcher struct {
	blockchain *chain.Blockchain
	consensus  *consensus.QuorumConsensus
	validators *validator.ValidatorRegistry
}

func NewPayloadWatcher(
	bc *chain.Blockchain,
	qc *consensus.QuorumConsensus,
	vr *validator.ValidatorRegistry,
) *PayloadWatcher {
	return &PayloadWatcher{
		blockchain: bc,
		consensus:  qc,
		validators: vr,
	}
}

type BlockchainPayload struct {
	ProposalID       string                 `json:"proposal_id"`
	CheckpointID     string                 `json:"checkpoint_id"`
	ToolName         string                 `json:"tool_name"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Decision         Decision               `json:"decision"`
	PriorityResult   PriorityResult         `json:"priority_result"`
	Timestamp        int64                  `json:"timestamp"`
}

type Decision struct {
	ProposalID      string `json:"proposal_id"`
	CheckpointID    string `json:"checkpoint_id"`
	Approved        bool   `json:"approved"`
	RejectionReason string `json:"rejection_reason"`
	DecisionBy      string `json:"decision_by"`
	Timestamp       int64  `json:"timestamp"`
}

type PriorityResult struct {
	Tier                string   `json:"tier"`
	RequiresApproval    bool     `json:"requires_approval"`
	AssignedDevelopers  []string `json:"assigned_developers"`
	AffectedDirectories []string `json:"affected_directories"`
	Reason              string   `json:"reason"`
	CheckpointID        string   `json:"checkpoint_id"`
}

func (pw *PayloadWatcher) Start() error {
	if err := os.MkdirAll(BlockchainMailbox, 0755); err != nil {
		return fmt.Errorf("failed to create blockchain mailbox: %w", err)
	}

	log.Printf("Blockchain payload watcher started")
	log.Printf("   Watching: %s", BlockchainMailbox)

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for range ticker.C {
		pw.processPayloads()
	}
	return nil
}

func (pw *PayloadWatcher) processPayloads() {
	pattern := filepath.Join(BlockchainMailbox, "payload_*.json")
	files, err := filepath.Glob(pattern)
	if err != nil {
		log.Printf("Error scanning blockchain mailbox: %v", err)
		return
	}

	for _, filePath := range files {
		if err := pw.handlePayload(filePath); err != nil {
			log.Printf("Error handling payload %s: %v", filePath, err)
		}
	}
}

func (pw *PayloadWatcher) handlePayload(filePath string) error {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read payload: %w", err)
	}

	var payload BlockchainPayload
	if err := json.Unmarshal(data, &payload); err != nil {
		return fmt.Errorf("failed to parse payload: %w", err)
	}

	log.Printf("Received blockchain payload:")
	log.Printf("   Proposal: %s", payload.ProposalID)
	log.Printf("   Tool: %s", payload.ToolName)
	log.Printf("   Decision: approved=%v", payload.Decision.Approved)

	blockData := block.BlockData{
		ProposalID:       payload.ProposalID,
		CheckpointID:     payload.CheckpointID,
		ToolName:         payload.ToolName,
		ToolArguments:    payload.ToolArguments,
		ReasoningSummary: payload.ReasoningSummary,
		Decision: block.Decision{
			Approved:        payload.Decision.Approved,
			DecisionBy:      payload.Decision.DecisionBy,
			RejectionReason: payload.Decision.RejectionReason,
			Timestamp:       payload.Decision.Timestamp,
		},
		Timestamp: payload.Timestamp,
	}

	newBlock, err := pw.blockchain.AddBlock(blockData)
	if err != nil {
		return fmt.Errorf("failed to add block: %w", err)
	}

	log.Printf("✓ Block created: #%d (hash: %s)", newBlock.Index, newBlock.Hash[:16]+"...")

	if err := pw.consensus.ProposeBlock(newBlock); err != nil {
		return fmt.Errorf("failed to propose block: %w", err)
	}

	activeValidators := pw.validators.GetActiveValidators()
	for _, v := range activeValidators {
		sig := block.Signature{
			ValidatorID:   v.ID,
			ValidatorName: v.Name,
			Signature:     v.SignBlock(newBlock.Hash),
			Tiemstamp:     time.Now().Unix(),
		}

		if err := pw.consensus.AddValidatorSignature(newBlock.Hash, sig); err != nil {
			continue
		}
	}

	hasQuorum, err := pw.consensus.HasQuorum(newBlock.Hash)
	if err != nil {
		return fmt.Errorf("failed to check quorum: %w", err)
	}

	if !hasQuorum {
		return nil
	}

	pw.consensus.RemovePending(newBlock.Hash)

	if err := pw.blockchain.SaveToFile("./data/blockchain.json"); err != nil {
		return fmt.Errorf("failed to save blockchain: %w", err)
	}

	response := map[string]interface{}{
		"approved":      payload.Decision.Approved,
		"proposal_id":   payload.ProposalID,
		"checkpoint_id": payload.CheckpointID,
		"block_hash":    newBlock.Hash,
		"block_index":   newBlock.Index,
		"timestamp":     time.Now().Unix(),
	}

	responseFile := filepath.Join(
		BlockchainMailbox,
		fmt.Sprintf("res_%s.json", payload.CheckpointID),
	)

	respData, _ := json.MarshalIndent(response, "", "  ")
	if err := os.WriteFile(responseFile, respData, 0644); err != nil {
		return fmt.Errorf("failed to write blockchain response: %w", err)
	}

	log.Printf("Blockchain decision written to: %s", responseFile)

	if err := os.Remove(filePath); err != nil {
		log.Printf("Warning: Failed to delete payload file: %v", err)
	}

	return nil
}
