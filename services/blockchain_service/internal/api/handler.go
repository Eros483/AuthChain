package api

import (
	"net/http"
	"time"

	"authchain/internal/block"
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/governance"
	"authchain/internal/solana"
	"authchain/internal/validator"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	governance *governance.ProposalStore
	tools      *governance.ToolRegistry
	owners     *governance.DirectoryOwnerRegistry
	blockchain *chain.Blockchain
	consensus  *consensus.QuorumConsensus
	validators *validator.ValidatorRegistry
}

func NewHandler(
	ps *governance.ProposalStore,
	tr *governance.ToolRegistry,
	or *governance.DirectoryOwnerRegistry,
	bc *chain.Blockchain,
	qc *consensus.QuorumConsensus,
	vr *validator.ValidatorRegistry,
) *Handler {
	return &Handler{
		governance: ps,
		tools:      tr,
		owners:     or,
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
	Timestamp        int64                  `json:"timestamp"`
}

type Decision struct {
	Approved        bool   `json:"approved"`
	DecisionBy      string `json:"decision_by"`
	RejectionReason string `json:"rejection_reason"`
	Timestamp       int64  `json:"timestamp"`
}

func extractPaths(args map[string]interface{}) []string {
	var paths []string

	if p, ok := args["path"].(string); ok {
		paths = append(paths, p)
	}

	if files, ok := args["files"].([]interface{}); ok {
		for _, f := range files {
			if s, ok := f.(string); ok {
				paths = append(paths, s)
			}
		}
	}

	return paths
}

/* ---------------- ACTION SUBMIT ---------------- */

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

	if h.tools.IsCritical(req.ToolName) {
		paths := extractPaths(req.ToolArguments)
		validatorSet := map[string]bool{}

		for _, p := range paths {
			for _, o := range h.owners.GetOwners(p) {
				validatorSet[o] = true
			}
		}

		var required []string
		for v := range validatorSet {
			required = append(required, v)
		}

		h.governance.Store(&governance.Proposal{
			ProposalID:         req.ProposalID,
			CheckpointID:       req.CheckpointID,
			ToolName:           req.ToolName,
			ToolArguments:      req.ToolArguments,
			ReasoningSummary:   req.ReasoningSummary,
			Status:             "pending",
			RequiredValidators: required,
			CreatedAt:          time.Now(),
		})
	}

	c.JSON(200, gin.H{"status": "submitted"})
}
func (h *Handler) ApproveOnSolana(c *gin.Context) {
	var req struct {
		ProposalID string `json:"proposal_id"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "invalid payload"})
		return
	}

	solana.MarkApproved(req.ProposalID)

	c.JSON(200, gin.H{
		"status":      "approved_on_solana",
		"proposal_id": req.ProposalID,
	})
}

/* ---------------- RECORD DECISION ---------------- */

func (h *Handler) RecordDecision(c *gin.Context) {
	var payload BlockchainPayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

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

	if payload.Decision.Approved {
		approved, _ := solana.IsExecutionApproved(payload.ProposalID)
		if !approved {
			c.JSON(403, gin.H{
				"error": "Execution not approved on Solana",
			})
			return
		}
	}

	newBlock, err := h.blockchain.AddBlock(blockData)
	if err != nil {
		c.JSON(500, gin.H{"error": "block creation failed"})
		return
	}

	h.consensus.ProposeBlock(newBlock)

	for range h.validators.GetActiveValidators() {
		_ = h.consensus.Approve(newBlock.Hash)
	}

	if !h.consensus.HasQuorum(newBlock.Hash) {
		c.JSON(http.StatusAccepted, gin.H{
			"status": "pending_quorum",
			"hash":   newBlock.Hash,
		})
		return
	}

	h.consensus.Remove(newBlock.Hash)
	_ = h.blockchain.SaveToFile("./data/blockchain.json")

	c.JSON(http.StatusCreated, gin.H{
		"status":      "finalized",
		"block_index": newBlock.Index,
		"block_hash":  newBlock.Hash,
	})
}

/* ---------------- QUERY BLOCKS ---------------- */

func (h *Handler) GetBlocks(c *gin.Context) {
	c.JSON(200, h.blockchain.Blocks)
}

func (h *Handler) GetBlock(c *gin.Context) {
	var req struct {
		Index uint64 `uri:"index"`
	}

	if c.ShouldBindUri(&req) != nil {
		c.JSON(400, gin.H{"error": "invalid index"})
		return
	}

	block, err := h.blockchain.GetBlock(req.Index)
	if err != nil {
		c.JSON(404, gin.H{"error": "block not found"})
		return
	}

	c.JSON(200, block)
}

func (h *Handler) GetBlockByProposal(c *gin.Context) {
	id := c.Param("proposal_id")
	blocks, _ := h.blockchain.FindByProposalID(id)
	c.JSON(200, blocks)
}

/* ---------------- VALIDATORS ---------------- */

func (h *Handler) AddValidator(c *gin.Context) {
	var req struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	}

	if c.ShouldBindJSON(&req) != nil {
		c.JSON(400, gin.H{"error": "invalid payload"})
		return
	}

	v := &validator.Validator{
		Wallet: req.ID,
		Name:   req.Name,
		Active: true,
	}

	_ = h.validators.AddValidator(v)
	c.JSON(201, v)
}

func (h *Handler) RemoveValidator(c *gin.Context) {
	id := c.Param("id")
	_ = h.validators.RemoveValidator(id)
	c.JSON(200, gin.H{"removed": id})
}

func (h *Handler) GetValidators(c *gin.Context) {
	c.JSON(200, h.validators.GetActiveValidators())
}

/* ---------------- HEALTH + VERIFY ---------------- */

func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(200, gin.H{
		"chain_length": h.blockchain.Length(),
		"validators":   len(h.validators.GetActiveValidators()),
	})
}

func (h *Handler) VerifyChain(c *gin.Context) {
	if err := h.blockchain.Verify(); err != nil {
		c.JSON(500, gin.H{"valid": false})
		return
	}
	c.JSON(200, gin.H{"valid": true})
}
