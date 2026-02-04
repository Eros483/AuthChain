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

const (
	AIMailbox     = "../../services/ipc_mailbox/ai"
	PolicyMailbox = "../../services/ipc_mailbox/policy"
)

type MailboxWatcher struct {
	evaluator     *policy.Evaluator
	proposalStore *proposal.ProposalStore
}

func NewMailboxWatcher(evaluator *policy.Evaluator, proposalStore *proposal.ProposalStore) *MailboxWatcher {
	return &MailboxWatcher{
		evaluator:     evaluator,
		proposalStore: proposalStore,
	}
}

func (mw *MailboxWatcher) Start() error {
	if err := os.MkdirAll(AIMailbox, 0755); err != nil {
		return fmt.Errorf("failed to create AI mailbox: %w", err)
	}
	if err := os.MkdirAll(PolicyMailbox, 0755); err != nil {
		return fmt.Errorf("failed to create Policy mailbox: %w", err)
	}

	log.Printf("Mailbox watcher started")
	log.Printf("   Watching: %s", AIMailbox)
	log.Printf("   Responding to: %s", PolicyMailbox)

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for range ticker.C {
		mw.processMailbox()
	}

	return nil
}

func (mw *MailboxWatcher) processMailbox() {
	pattern := filepath.Join(AIMailbox, "req_*.json")
	files, err := filepath.Glob(pattern)
	if err != nil {
		log.Printf("Error scanning mailbox: %v", err)
		return
	}

	for _, filePath := range files {
		if err := mw.handleRequest(filePath); err != nil {
			log.Printf("Error handling %s: %v", filePath, err)
		}
	}
}

type AIRequest struct {
	ToolName         string                 `json:"tool_name"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Timestamp        string                 `json:"timestamp"`
	CheckpointID     string                 `json:"checkpoint_id"`
}

func (mw *MailboxWatcher) handleRequest(filePath string) error {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	var aiReq AIRequest
	if err := json.Unmarshal(data, &aiReq); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}

	log.Printf("Received proposal from AI:")
	log.Printf("   Tool: %s", aiReq.ToolName)
	log.Printf("   Checkpoint: %s", aiReq.CheckpointID)

	proposalID := fmt.Sprintf("prop-%s", aiReq.CheckpointID[:8])

	facts := policy.ProposalFacts{
		ProposalID:       proposalID,
		ThreadID:         aiReq.CheckpointID,
		CheckpointID:     aiReq.CheckpointID,
		ToolName:         aiReq.ToolName,
		ToolArguments:    aiReq.ToolArguments,
		ReasoningSummary: aiReq.ReasoningSummary,
		Timestamp:        time.Now().Unix(),
		FilesChanged:     []string{},
		LinesAdded:       0,
		LinesRemoved:     0,
	}

	result := mw.evaluator.EvaluatePriority(facts)

	log.Printf("✓ Evaluation complete:")
	log.Printf("   Tier: %s", result.Tier)
	log.Printf("   Requires Approval: %v", result.RequiresApproval)

	if result.RequiresApproval {
		if err := mw.proposalStore.Store(facts, result); err != nil {
			log.Printf("Warning: Failed to store proposal: %v", err)
		} else {
			log.Printf("✓ Stored proposal %s (status: pending)", proposalID)
		}
	}

	response := map[string]interface{}{
		"tier":                 result.Tier,
		"requires_approval":    result.RequiresApproval,
		"assigned_developers":  result.AssignedDevelopers,
		"affected_directories": result.AffectedDirectories,
		"reason":               result.Reason,
		"proposal_id":          proposalID,
	}

	responseFile := filepath.Join(PolicyMailbox, fmt.Sprintf("res_%s.json", aiReq.CheckpointID))
	responseData, err := json.MarshalIndent(response, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal response: %w", err)
	}

	if err := os.WriteFile(responseFile, responseData, 0644); err != nil {
		return fmt.Errorf("failed to write response: %w", err)
	}

	log.Printf("Response sent to: %s", responseFile)

	if err := os.Remove(filePath); err != nil {
		log.Printf("Warning: Failed to delete request file: %v", err)
	}

	return nil
}
