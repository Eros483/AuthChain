package api

import (
	"encoding/json"
	"net/http"
	"policyservice/internal/policy"
	"policyservice/internal/storage"
)

type Handler struct {
	evaluator *policy.Evaluator
	store     *storage.PolicyStore
}

func NewHandler(store *storage.PolicyStore) *Handler {
	return &Handler{
		evaluator: policy.NewEvaluator(store),
		store:     store,
	}
}

func (h *Handler) EvaluateProposal(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	var facts policy.ProposalFacts
	if err := json.NewDecoder(r.Body).Decode(&facts); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result := h.evaluator.EvaluatePriority(facts)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *Handler) AddDirOwnership(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	var ownership storage.DirectoryOwnership
	if err := json.NewDecoder(r.Body).Decode(&ownership); err != nil {
		http.Error(w, "Invalid Request Body", http.StatusBadRequest)
		return
	}

	if err := h.store.AddDirectoryOwnership(ownership); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

func (h *Handler) RemoveDirOwnership(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	dir := r.URL.Query().Get("directory")
	if dir == "" {
		http.Error(w, "dir parameter req", http.StatusBadRequest)
		return
	}

	if err := h.store.RemoveDirectoryOwnership(dir); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}
func (h *Handler) GetAllOwnerships(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	ownerships := h.store.GetAllOwnership()

	w.Header().Set("Content-type", "application/json")
	json.NewEncoder(w).Encode(ownerships)
}

func (h *Handler) UpdateLineThreshold(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPut {
		http.Error(w, "Mthod Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Threshold int `json:"threshold"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid Req Body", http.StatusBadRequest)
		return
	}

	if err := h.store.UpdateLineThreshold(req.Threshold); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}
