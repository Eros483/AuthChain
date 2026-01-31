package main

import (
	"log"
	"policyservice/internal/ipc"
	"policyservice/internal/proposal"
	"policyservice/internal/storage"
	"time"
)

func main() {
	policyStore := storage.NewPolicyStore()
	proposalStore := proposal.NewProposalStore()

	go func() {
		ticker := time.NewTicker(1 * time.Hour)
		defer ticker.Stop()

		for range ticker.C {
			removed := proposalStore.Cleanup(24 * time.Hour)
			if removed > 0 {
				log.Printf("Cleaned up %d old proposals", removed)
			}
		}
	}()

	socketPath := "/tmp/policy-service.sock"
	handler := ipc.NewIPCHandler(policyStore, proposalStore, socketPath)

	log.Println("Policy Service starting with IPC on", socketPath)
	if err := handler.Start(); err != nil {
		log.Fatal(err)
	}
}
