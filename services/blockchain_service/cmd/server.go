package main

import (
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/mailbox"
	"authchain/internal/validator"
	"log"
	"os"
)

func main() {
	log.Println("AuthChain Blockchain Service Starting")

	if err := os.MkdirAll("./data", 0755); err != nil {
		log.Fatal("Failed to create data directory:", err)
	}

	blockchain, err := chain.LoadFromFile("./data/blockchain.json")
	if err != nil {
		log.Printf("Creating new blockchain: %v", err)
		blockchain = chain.NewBlockchain()
	}
	log.Printf("✓ Blockchain loaded (length: %d)", blockchain.Length())

	validatorRegistry := validator.NewValidatorRegistry()

	quorumConsensus := consensus.NewQuorumConsensus(validatorRegistry)
	log.Printf("✓ Consensus mechanism initialized")

	payloadWatcher := mailbox.NewPayloadWatcher(
		blockchain,
		quorumConsensus,
		validatorRegistry,
	)

	log.Println("Starting payload watcher...")
	if err := payloadWatcher.Start(); err != nil {
		log.Fatal("Payload watcher error:", err)
	}
}
