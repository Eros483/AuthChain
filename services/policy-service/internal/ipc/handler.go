package ipc

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"policyservice/internal/policy"
	"policyservice/internal/storage"
)

type IPCHandler struct {
	evaluator  *policy.Evaluator
	store      *storage.PolicyStore
	socketPath string
}

func NewIPCHandler(store *storage.PolicyStore, socketPath string) *IPCHandler {
	return &IPCHandler{
		evaluator:  policy.NewEvaluator(store),
		store:      store,
		socketPath: socketPath,
	}
}

// Action : "evaluate", "add_dir", "remove_dir", "get_dirs", "decision"
type IPCRequest struct {
	Action string          `json:"action"`
	Data   json.RawMessage `json:"data"`
}

type IPCResponse struct {
	Success bool            `json:"success"`
	Data    json.RawMessage `json:"data,omitempty"`
	Error   string          `json:"error,omitempty"`
}

func (h *IPCHandler) Start() error {
	if err := os.RemoveAll(h.socketPath); err != nil {
		return fmt.Errorf("failed to remove existing socket: %w", err)
	}

	listener, err := net.Listen("unix", h.socketPath)
	if err != nil {
		return fmt.Errorf("failed to listen on socket: %w", err)
	}
	defer listener.Close()

	if err := os.Chmod(h.socketPath, 0660); err != nil {
		return fmt.Errorf("failed to set socket permissions: %w", err)
	}

	log.Printf("IPC server listening on %s", h.socketPath)

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go h.handleConnection(conn)
	}
}

func (h *IPCHandler) handleConnection(conn net.Conn) {
	defer conn.Close()

	decoder := json.NewDecoder(conn)
	encoder := json.NewEncoder(conn)

	var req IPCRequest
	if err := decoder.Decode(&req); err != nil {
		h.sendError(encoder, fmt.Sprintf("failed to decode request: %v", err))
		return
	}

	switch req.Action {
	case "evaluate":
		h.handleEvaluate(encoder, req.Data)
	case "decision":
		h.handleDecision(encoder, req.Data)
	case "add_dir":
		h.handleAddDir(encoder, req.Data)
	case "remove_dir":
		h.handleRemoveDir(encoder, req.Data)
	case "get_dirs":
		h.handleGetDirs(encoder)
	case "update_threshold":
		h.handleUpdateThreshold(encoder, req.Data)
	default:
		h.sendError(encoder, "unknown action")
	}
}

func (h *IPCHandler) handleEvaluate(encoder *json.Encoder, data json.RawMessage) {
	var facts policy.ProposalFacts
	if err := json.Unmarshal(data, &facts); err != nil {
		h.sendError(encoder, fmt.Sprintf("invalid proposal facts: %v", err))
		return
	}

	result := h.evaluator.EvaluatePriority(facts)

	resultData, _ := json.Marshal(result)
	encoder.Encode(IPCResponse{
		Success: true,
		Data:    resultData,
	})
}

func (h *IPCHandler) handleDecision(encoder *json.Encoder, data json.RawMessage) {
	var decision policy.ApprovalDecision
	if err := json.Unmarshal(data, &decision); err != nil {
		h.sendError(encoder, fmt.Sprintf("invalid decision: %v", err))
		return
	}

	if !decision.Approved && decision.RejectionReason == "" {
		h.sendError(encoder, "rejection reason is required when proposal is rejected")
		return
	}

	log.Printf("Decision received for proposal %s: approved=%v, reason=%s",
		decision.ProposalID, decision.Approved, decision.RejectionReason)

	// TODO: Send to blockchain via IPC
	// payload := policy.BlockchainPayload{
	//     ProposalID: decision.ProposalID,
	//     Decision: decision,
	// }
	// sendToBlockchain(payload)

	responseData, _ := json.Marshal(map[string]string{
		"status":      "decision recorded",
		"proposal_id": decision.ProposalID,
	})

	encoder.Encode(IPCResponse{
		Success: true,
		Data:    responseData,
	})
}

func (h *IPCHandler) handleAddDir(encoder *json.Encoder, data json.RawMessage) {
	var ownership storage.DirectoryOwnership
	if err := json.Unmarshal(data, &ownership); err != nil {
		h.sendError(encoder, fmt.Sprintf("invalid directory ownership: %v", err))
		return
	}

	if err := h.store.AddDirectoryOwnership(ownership); err != nil {
		h.sendError(encoder, err.Error())
		return
	}

	encoder.Encode(IPCResponse{Success: true})
}

func (h *IPCHandler) handleRemoveDir(encoder *json.Encoder, data json.RawMessage) {
	var req struct {
		Directory string `json:"directory"`
	}
	if err := json.Unmarshal(data, &req); err != nil {
		h.sendError(encoder, fmt.Sprintf("invalid request: %v", err))
		return
	}

	if err := h.store.RemoveDirectoryOwnership(req.Directory); err != nil {
		h.sendError(encoder, err.Error())
		return
	}

	encoder.Encode(IPCResponse{Success: true})
}

func (h *IPCHandler) handleGetDirs(encoder *json.Encoder) {
	ownerships := h.store.GetAllOwnership()
	data, _ := json.Marshal(ownerships)

	encoder.Encode(IPCResponse{
		Success: true,
		Data:    data,
	})
}

func (h *IPCHandler) handleUpdateThreshold(encoder *json.Encoder, data json.RawMessage) {
	var req struct {
		Threshold int `json:"threshold"`
	}
	if err := json.Unmarshal(data, &req); err != nil {
		h.sendError(encoder, fmt.Sprintf("invalid request: %v", err))
		return
	}

	if err := h.store.UpdateLineThreshold(req.Threshold); err != nil {
		h.sendError(encoder, err.Error())
		return
	}

	encoder.Encode(IPCResponse{Success: true})
}

func (h *IPCHandler) sendError(encoder *json.Encoder, errMsg string) {
	encoder.Encode(IPCResponse{
		Success: false,
		Error:   errMsg,
	})
}
