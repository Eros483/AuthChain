package storage

type ToolRegistry struct {
	SafeTools     map[string]bool
	CriticalTools map[string]bool
}

func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{
		SafeTools: map[string]bool{
			"read_file":            true,
			"list_directory":       true,
			"search_codebase":      true,
			"git_log":              true,
			"git_diff":             true,
			"git_status":           true,
			"read_database":        true,
			"sql_db_list_tables":   true,
			"sql_db_schema":        true,
			"sql_db_query_checker": true,
		},
		CriticalTools: map[string]bool{
			"deploy_to_production": true,
			"delete_database":      true,
			"git_push_commit":      true,
			"edit_database":        true,
			"write_file":           true,
			"delete_file":          true,
			"sql_db_query":         true,
		},
	}
}

func (tr *ToolRegistry) GetToolTier(toolName string) string {
	if tr.SafeTools[toolName] {
		return "tier_safe"
	}
	if tr.CriticalTools[toolName] {
		return "tier_critical"
	}
	return "tier_critical"
}

func (tr *ToolRegistry) IsCritical(toolName string) bool {
	return tr.GetToolTier(toolName) == "tier_critical"
}
