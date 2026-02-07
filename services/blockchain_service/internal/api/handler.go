package api

import (
	"log"
	"net/http"
	"time"

	"authchain/internal/block"
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/governance"
	"authchain/internal/validator"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	governance *governance.ProposalStore
	tools      *governance.ToolRegistry
	blockchain *chain.Blockchain
	consensus  *consensus.QuorumConsensus
	validators *validator.ValidatorRegistry
}

func NewHandler(
	ps *governance.ProposalStore,
	tr *governance.ToolRegistry,
	bc *chain.Blockchain,
	qc *consensus.QuorumConsensus,
	vr *validator.ValidatorRegistry,
) *Handler {
	return &Handler{
		governance: ps,
		tools:      tr,
		blockchain: bc,
		consensus:  qc,
		validators: vr,
	}
}

type BlockchainPayload struct {
	ProposalID       string                 `json:"proposal_id" binding:"required"`
	CheckpointID     string                 `json:"checkpoint_id" binding:"required"`
	ToolName         string                 `json:"tool_name" binding:"required"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Decision         Decision               `json:"decision" binding:"required"`
	PriorityResult   PriorityResult         `json:"priority_result"`
	Timestamp        int64                  `json:"timestamp"`
}

type Decision struct {
	ProposalID      string `json:"proposal_id"`
	CheckpointID    string `json:"checkpoint_id"`
	Approved        bool   `json:"approved"`
	RejectionReason string `json:"rejection_reason"`
	DecisionBy      string `json:"decision_by" binding:"required"`
	Timestamp       int64  `json:"timestamp"`
}

type PriorityResult struct {
	Tier             string `json:"tier"`
	RequiresApproval bool   `json:"requires_approval"`
	Reason           string `json:"reason"`
	CheckpointID     string `json:"checkpoint_id"`
}

func (h *Handler) SubmitAction(c *gin.Context) {
	var req struct {
		ProposalID       string                 `json:"proposal_id"`
		CheckpointID     string                 `json:"checkpoint_id"`
		ToolName         string                 `json:"tool_name"`
		ToolArguments    map[string]interface{} `json:"tool_arguments"`
		ReasoningSummary string                 `json:"reasoning_summary"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	isCritical := h.tools.IsCritical(req.ToolName)

	if isCritical {
		h.governance.Store(&governance.Proposal{
			ProposalID:       req.ProposalID,
			CheckpointID:     req.CheckpointID,
			ToolName:         req.ToolName,
			ToolArguments:    req.ToolArguments,
			ReasoningSummary: req.ReasoningSummary,
			Status:           "pending",
			CreatedAt:        time.Now(),
		})
	}

	c.JSON(200, gin.H{
		"critical": isCritical,
		"status":   "submitted",
	})
}

func (h *Handler) RecordDecision(c *gin.Context) {
	var payload BlockchainPayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
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

	newBlock, err := h.blockchain.AddBlock(blockData)
	if err != nil {
		log.Printf("Failed to add block: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create block"})
		return
	}

	log.Printf("✓ Block created: #%d (hash: %s)", newBlock.Index, newBlock.Hash[:16]+"...")

	if err := h.governance.Resolve(
		payload.ProposalID,
		payload.Decision.Approved,
		payload.Decision.DecisionBy,
	); err != nil {
		log.Printf("Warning: failed to resolve proposal: %v", err)
	}

	if err := h.consensus.ProposeBlock(newBlock); err != nil {
		log.Printf("Failed to propose block: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to propose block"})
		return
	}

	activeValidators := h.validators.GetActiveValidators()
	for _, v := range activeValidators {
		sig := block.Signature{
			ValidatorID:   v.ID,
			ValidatorName: v.Name,
			Signature:     v.SignBlock(newBlock.Hash),
			Tiemstamp:     time.Now().Unix(),
		}

		if err := h.consensus.AddValidatorSignature(newBlock.Hash, sig); err != nil {
			log.Printf("Validator %s signature failed: %v", v.Name, err)
			continue
		}

		log.Printf("✓ Validator %s signed block", v.Name)
	}

	hasQuorum, err := h.consensus.HasQuorum(newBlock.Hash)
	if err != nil {
		log.Printf("Failed to check quorum: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "consensus check failed"})
		return
	}

	if !hasQuorum {
		c.JSON(http.StatusAccepted, gin.H{
			"status":      "pending",
			"block_index": newBlock.Index,
			"block_hash":  newBlock.Hash,
			"message":     "Block created, awaiting quorum",
		})
		return
	}

	log.Printf("QUORUM REACHED - Block #%d finalized", newBlock.Index)

	h.consensus.RemovePending(newBlock.Hash)

	if err := h.blockchain.SaveToFile("./services/blockchain_service/data/blockchain.json"); err != nil {
		log.Printf(" Failed to save blockchain: %v", err)
	} else {
		log.Printf("Blockchain saved (length: %d)", h.blockchain.Length())
	}

	c.JSON(http.StatusCreated, gin.H{
		"status":        "finalized",
		"approved":      payload.Decision.Approved,
		"proposal_id":   payload.ProposalID,
		"checkpoint_id": payload.CheckpointID,
		"block_hash":    newBlock.Hash,
		"block_index":   newBlock.Index,
		"validators":    len(activeValidators),
		"timestamp":     time.Now().Unix(),
	})
}

func (h *Handler) GetBlocks(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"blocks": h.blockchain.Blocks,
		"length": h.blockchain.Length(),
	})
}

func (h *Handler) GetBlock(c *gin.Context) {
	var req struct {
		Index uint64 `uri:"index" binding:"required"`
	}

	if err := c.ShouldBindUri(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid index"})
		return
	}

	block, err := h.blockchain.GetBlock(req.Index)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "block not found"})
		return
	}

	c.JSON(http.StatusOK, block)
}

func (h *Handler) GetBlockByProposal(c *gin.Context) {
	proposalID := c.Param("proposal_id")

	blocks, err := h.blockchain.FindByProposalID(proposalID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no blocks found for proposal"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"proposal_id": proposalID,
		"blocks":      blocks,
		"count":       len(blocks),
	})
}

func (h *Handler) AddValidator(c *gin.Context) {
	var req struct {
		ID        string `json:"id" binding:"required"`
		Name      string `json:"name" binding:"required"`
		PublicKey string `json:"public_key"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	v := &validator.Validator{
		ID:        req.ID,
		Name:      req.Name,
		PublicKey: req.PublicKey,
		Active:    true,
	}

	if err := h.validators.AddValidator(v); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Printf("✓ Validator registered: %s (ID: %s)", v.Name, v.ID)

	c.JSON(http.StatusCreated, gin.H{
		"message":     "validator added",
		"validator":   v,
		"quorum_size": h.validators.GetQuorumSize(),
	})
}
func (h *Handler) RemoveValidator(c *gin.Context) {
	id := c.Param("id")

	if err := h.validators.RemoveValidator(id); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	log.Printf("Validator deactivated: %s", id)

	c.JSON(http.StatusOK, gin.H{
		"message":      "validator deactivated",
		"validator_id": id,
		"quorum_size":  h.validators.GetQuorumSize(),
	})
}
func (h *Handler) GetValidators(c *gin.Context) {
	active := h.validators.GetActiveValidators()
	c.JSON(http.StatusOK, gin.H{
		"validators":  active,
		"count":       len(active),
		"quorum_size": h.validators.GetQuorumSize(),
	})
}

func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":       "healthy",
		"service":      "blockchain-service",
		"chain_length": h.blockchain.Length(),
		"validators":   len(h.validators.GetActiveValidators()),
		"quorum_size":  h.validators.GetQuorumSize(),
		"latest_block": h.blockchain.GetLatestBlock().Index,
		"latest_hash":  h.blockchain.GetLatestBlock().Hash[:16] + "...",
	})
}

func (h *Handler) VerifyChain(c *gin.Context) {
	if err := h.blockchain.Verify(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"valid": false,
			"error": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"valid":  true,
		"length": h.blockchain.Length(),
	})
}
