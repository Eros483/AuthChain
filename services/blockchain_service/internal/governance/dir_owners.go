package governance

type DirectoryOwnerRegistry struct {
	owners map[string][]string
}

func NewDirectoryOwnerRegistry() *DirectoryOwnerRegistry {
	return &DirectoryOwnerRegistry{
		owners: map[string][]string{
			"src/auth": {"alice", "bob"},
			"src/db":   {"carol"},
			"scripts":  {"devops"},
		},
	}
}

func (r *DirectoryOwnerRegistry) GetOwners(path string) []string {
	for dir, owners := range r.owners {
		if len(path) >= len(dir) && path[:len(dir)] == dir {
			return owners
		}
	}
	return nil
}
