package mailbox

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"policyservice/internal/policy"
	"policyservice/internal/proposal"
)

const IPC_ROOT = "../../services/ipc_mailbox"

const (
	DecisionMailbox   = IPC_ROOT + "/decisions"
	BlockchainMailbox = IPC_ROOT + "/blockchain"
)

type DecisionWatcher struct {
	proposalStore *proposal.ProposalStore
}

func NewDecisionWatcher(proposalStore *proposal.ProposalStore) *DecisionWatcher {
	return &DecisionWatcher{
		proposalStore: proposalStore,
	}
}

type HumanDecision struct {
	ProposalID      string `json:"proposal_id"`
	CheckpointID    string `json:"checkpoint_id"`
	Approved        bool   `json:"approved"`
	RejectionReason string `json:"rejection_reason,omitempty"`
	DecisionBy      string `json:"decision_by"`
}

func (dw *DecisionWatcher) Start() error {
	if err := os.MkdirAll(DecisionMailbox, 0755); err != nil {
		return fmt.Errorf("failed to create decision mailbox: %w", err)
	}

	log.Printf("Decision watcher started")
	log.Printf("   Watching: %s", DecisionMailbox)

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for range ticker.C {
		dw.processDecisions()
	}

	return nil
}

func (dw *DecisionWatcher) processDecisions() {
	pattern := filepath.Join(DecisionMailbox, "decision_*.json")
	files, err := filepath.Glob(pattern)
	if err != nil {
		log.Printf("Error scanning decisions: %v", err)
		return
	}

	for _, filePath := range files {
		if err := dw.handleDecision(filePath); err != nil {
			log.Printf("Error handling decision %s: %v", filePath, err)
		}
	}
}

func (dw *DecisionWatcher) handleDecision(filePath string) error {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	var decision HumanDecision
	if err := json.Unmarshal(data, &decision); err != nil {
		return fmt.Errorf("failed to parse decision: %w", err)
	}

	log.Printf("Human decision received:")
	log.Printf("   Proposal: %s", decision.ProposalID)
	log.Printf("   Approved: %v", decision.Approved)

	if !decision.Approved && decision.RejectionReason == "" {
		return fmt.Errorf("rejection reason required when rejecting")
	}

	storedProposal, err := dw.proposalStore.Get(decision.ProposalID)
	if err != nil {
		return fmt.Errorf("proposal not found: %w", err)
	}

	if err := dw.proposalStore.MarkResolved(decision.ProposalID, decision.Approved); err != nil {
		log.Printf("Warning: Failed to mark resolved: %v", err)
	}

	blockchainPayload := policy.BlockchainPayload{
		ProposalID:       decision.ProposalID,
		CheckpointID:     decision.CheckpointID,
		ToolName:         storedProposal.Facts.ToolName,
		ToolArguments:    storedProposal.Facts.ToolArguments,
		ReasoningSummary: storedProposal.Facts.ReasoningSummary,
		Decision: policy.ApprovalDecision{
			ProposalID:      decision.ProposalID,
			CheckpointID:    decision.CheckpointID,
			Approved:        decision.Approved,
			RejectionReason: decision.RejectionReason,
			DecisionBy:      decision.DecisionBy,
			Timestamp:       time.Now().Unix(),
		},
		PriorityResult: storedProposal.Result,
		Timestamp:      time.Now().Unix(),
	}

	log.Printf("✓ Blockchain payload ready:")
	log.Printf("   Tool: %s", blockchainPayload.ToolName)
	log.Printf("   Decision: %v", decision.Approved)

	blockchainFile := filepath.Join(
		BlockchainMailbox,
		fmt.Sprintf("payload_%s.json", decision.ProposalID),
	)
	payloadData, _ := json.MarshalIndent(blockchainPayload, "", "  ")
	os.MkdirAll(filepath.Dir(blockchainFile), 0755)
	os.WriteFile(blockchainFile, payloadData, 0644)

	log.Printf("Blockchain payload written to: %s", blockchainFile)

	// aiResponseFile := filepath.Join(PolicyMailbox, fmt.Sprintf("res_%s.json", decision.CheckpointID))
	// aiResponse := map[string]interface{}{
	// 	"approved": decision.Approved,
	// 	"reason":   decision.RejectionReason,
	// }
	// aiResponseData, _ := json.MarshalIndent(aiResponse, "", "  ")
	// os.WriteFile(aiResponseFile, aiResponseData, 0644)

	os.Remove(filePath)

	return nil
}
