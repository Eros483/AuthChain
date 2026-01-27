package main

import (
	"log"
	"net/http"
	"policyservice/internal/api"
	"policyservice/internal/storage"
)

func main() {
	store := storage.NewPolicyStore()
	handler := api.NewHandler(store)

	http.HandleFunc("/api/evaluate", handler.EvaluateProposal)
	http.HandleFunc("/api/admin/dir-ownership", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			handler.AddDirOwnership(w, r)

		case http.MethodDelete:
			handler.RemoveDirOwnership(w, r)

		case http.MethodGet:
			handler.GetAllOwnerships(w, r)

		default:
			http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		}
	})
	http.HandleFunc("/api/admin/line-threshold", handler.UpdateLineThreshold)

	log.Println("Policy Server Starting on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
