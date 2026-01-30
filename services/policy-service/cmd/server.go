package main

import (
	"log"
	"policyservice/internal/ipc"
	"policyservice/internal/storage"
)

func main() {
	store := storage.NewPolicyStore()

	socketPath := "/tmp/policy-service.sock"
	handler := ipc.NewIPCHandler(store, socketPath)

	log.Println("Policy Service starting with IPC on", socketPath)
	if err := handler.Start(); err != nil {
		log.Fatal(err)
	}
}
