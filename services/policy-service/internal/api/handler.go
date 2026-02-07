package api

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"time"

	"policyservice/internal/policy"
	"policyservice/internal/proposal"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	evaluator     *policy.Evaluator
	proposalStore *proposal.ProposalStore
}

func NewHandler(evaluator *policy.Evaluator, proposalStore *proposal.ProposalStore) *Handler {
	return &Handler{
		evaluator:     evaluator,
		proposalStore: proposalStore,
	}
}

func (h *Handler) EvaluateProposal(c *gin.Context) {
	var req struct {
		ToolName         string                 `json:"tool_name" binding:"required"`
		ToolArguments    map[string]interface{} `json:"tool_arguments"`
		ReasoningSummary string                 `json:"reasoning_summary"`
		CheckpointID     string                 `json:"checkpoint_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Printf("Received proposal from AI:")
	log.Printf("   Tool: %s", req.ToolName)
	log.Printf("   Checkpoint: %s", req.CheckpointID)

	proposalID := "prop-" + req.CheckpointID[:8]

	facts := policy.ProposalFacts{
		ProposalID:       proposalID,
		ThreadID:         req.CheckpointID,
		CheckpointID:     req.CheckpointID,
		ToolName:         req.ToolName,
		ToolArguments:    req.ToolArguments,
		ReasoningSummary: req.ReasoningSummary,
		Timestamp:        time.Now().Unix(),
		FilesChanged:     []string{},
		LinesAdded:       0,
		LinesRemoved:     0,
	}

	result := h.evaluator.EvaluatePriority(facts)

	log.Printf("✓ Evaluation complete:")
	log.Printf("   Tier: %s", result.Tier)
	log.Printf("   Requires Approval: %v", result.RequiresApproval)

	if result.RequiresApproval {
		if err := h.proposalStore.Store(facts, result); err != nil {
			log.Printf("Failed to store proposal: %v", err)
		} else {
			log.Printf("✓ Stored proposal %s (status: pending)", proposalID)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"proposal_id":       proposalID,
		"tier":              result.Tier,
		"requires_approval": result.RequiresApproval,
		"reason":            result.Reason,
		"checkpoint_id":     result.CheckpointID,
	})
}
func (h *Handler) SubmitDecision(c *gin.Context) {

	var req struct {
		ProposalID      string `json:"proposal_id" binding:"required"`
		CheckpointID    string `json:"checkpoint_id" binding:"required"`
		Approved        bool   `json:"approved"`
		RejectionReason string `json:"rejection_reason"`
		DecisionBy      string `json:"decision_by" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if !req.Approved && req.RejectionReason == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "rejection_reason required when rejecting"})
		return
	}

	log.Printf("Human decision received:")
	log.Printf("   Proposal: %s", req.ProposalID)
	log.Printf("   Approved: %v", req.Approved)

	storedProposal, err := h.proposalStore.Get(req.ProposalID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "proposal not found"})
		return
	}

	if err := h.proposalStore.MarkResolved(req.ProposalID, req.Approved); err != nil {
		log.Printf("Warning: Failed to mark resolved: %v", err)
	}

	blockchainPayload := policy.BlockchainPayload{
		ProposalID:       req.ProposalID,
		CheckpointID:     req.CheckpointID,
		ToolName:         storedProposal.Facts.ToolName,
		ToolArguments:    storedProposal.Facts.ToolArguments,
		ReasoningSummary: storedProposal.Facts.ReasoningSummary,
		Decision: policy.ApprovalDecision{
			ProposalID:      req.ProposalID,
			CheckpointID:    req.CheckpointID,
			Approved:        req.Approved,
			RejectionReason: req.RejectionReason,
			DecisionBy:      req.DecisionBy,
			Timestamp:       time.Now().Unix(),
		},
		PriorityResult: storedProposal.Result,
		Timestamp:      time.Now().Unix(),
	}

	blockchainURL := "http://localhost:8081/api/blocks"
	payloadJSON, _ := json.Marshal(blockchainPayload)

	resp, err := http.Post(blockchainURL, "application/json", bytes.NewBuffer(payloadJSON))
	if err != nil {
		log.Printf("Failed to send to blockchain: %v", err)
	} else {
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)

		if resp.StatusCode == http.StatusCreated {
			log.Printf("Blockchain recorded decision successfully")
			log.Printf("   Response: %s", string(body))
		} else {
			log.Printf("Blockchain responded with status %d: %s", resp.StatusCode, string(body))
		}
	}

	log.Printf("✓ Blockchain payload ready:")
	log.Printf("   Tool: %s", blockchainPayload.ToolName)
	log.Printf("   Decision: %v", req.Approved)

	c.JSON(http.StatusOK, gin.H{
		"status":        "decision recorded",
		"proposal_id":   req.ProposalID,
		"approved":      req.Approved,
		"checkpoint_id": req.CheckpointID,
	})
}

func (h *Handler) GetPendingProposals(c *gin.Context) {
	pending := h.proposalStore.GetPending()
	c.JSON(http.StatusOK, gin.H{
		"pending": pending,
		"count":   len(pending),
	})
}

func (h *Handler) HealthCheck(c *gin.Context) {
	counts := h.proposalStore.Count()
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"service":   "policy-service",
		"proposals": counts,
	})
}
