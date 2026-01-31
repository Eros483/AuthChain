package ipc

import (
	"encoding/json"
	"fmt"
	"net"
	"policyservice/internal/policy"
	"policyservice/internal/proposal"
	"policyservice/internal/storage"
)

type IPCClient struct {
	socketPath string
}

func NewIPCClient(socketPath string) *IPCClient {
	return &IPCClient{socketPath: socketPath}
}

func (c *IPCClient) sendRequest(action string, data interface{}) (*IPCResponse, error) {
	conn, err := net.Dial("unix", c.socketPath)
	if err != nil {
		return nil, fmt.Errorf("failed to connect: %w", err)
	}
	defer conn.Close()

	dataBytes, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal data: %w", err)
	}

	req := IPCRequest{
		Action: action,
		Data:   dataBytes,
	}

	encoder := json.NewEncoder(conn)
	decoder := json.NewDecoder(conn)

	if err := encoder.Encode(req); err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}

	var resp IPCResponse
	if err := decoder.Decode(&resp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &resp, nil
}

func (c *IPCClient) EvaluateProposal(facts policy.ProposalFacts) (*policy.PriorityResult, error) {
	resp, err := c.sendRequest("evaluate", facts)
	if err != nil {
		return nil, err
	}

	if !resp.Success {
		return nil, fmt.Errorf("evaluation failed: %s", resp.Error)
	}

	var result policy.PriorityResult
	if err := json.Unmarshal(resp.Data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse result: %w", err)
	}

	return &result, nil
}

func (c *IPCClient) SubmitDecision(decision policy.ApprovalDecision) error {
	resp, err := c.sendRequest("decision", decision)
	if err != nil {
		return err
	}

	if !resp.Success {
		return fmt.Errorf("decision submission failed: %s", resp.Error)
	}

	return nil
}

func (c *IPCClient) GetPendingProposals() ([]*proposal.StoredProposal, error) {
	resp, err := c.sendRequest("get_pending", nil)
	if err != nil {
		return nil, err
	}

	if !resp.Success {
		return nil, fmt.Errorf("failed to get pending proposals: %s", resp.Error)
	}

	var proposals []*proposal.StoredProposal
	if err := json.Unmarshal(resp.Data, &proposals); err != nil {
		return nil, fmt.Errorf("failed to parse proposals: %w", err)
	}

	return proposals, nil
}

func (c *IPCClient) AddDirectoryOwnership(ownership storage.DirectoryOwnership) error {
	resp, err := c.sendRequest("add_dir", ownership)
	if err != nil {
		return err
	}

	if !resp.Success {
		return fmt.Errorf("failed to add directory: %s", resp.Error)
	}

	return nil
}

func (c *IPCClient) GetAllOwnerships() ([]storage.DirectoryOwnership, error) {
	resp, err := c.sendRequest("get_dirs", nil)
	if err != nil {
		return nil, err
	}

	if !resp.Success {
		return nil, fmt.Errorf("failed to get ownerships: %s", resp.Error)
	}

	var ownerships []storage.DirectoryOwnership
	if err := json.Unmarshal(resp.Data, &ownerships); err != nil {
		return nil, fmt.Errorf("failed to parse ownerships: %w", err)
	}

	return ownerships, nil
}
