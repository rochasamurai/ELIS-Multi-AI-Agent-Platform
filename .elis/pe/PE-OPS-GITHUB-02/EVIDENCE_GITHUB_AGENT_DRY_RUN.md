# PE-OPS-GITHUB-02 GitHub Agent Dry-Run Evidence

## Baseline
- credential source: /opt/elis/secrets/github-agent.env
- expected identity: elis-git-bot
- fixed workspace: /opt/elis/agent-worktrees/github-agent
- repo: rochasamurai/ELIS-Multi-AI-Agent-Platform

## Commands
### gh auth status
github.com
  ✓ Logged in to github.com account rochasamurai (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token: [REDACTED — ambient rochasamurai token prefix removed before preservation]

### gh api /user --jq .login
rochasamurai

### gh repo view
{"nameWithOwner":"rochasamurai/ELIS-Multi-AI-Agent-Platform","viewerPermission":"ADMIN"}

### gh pr list
420	PM-CHORE-91: open PE-OPS-GITHUB-02	feature/pe-ops-github-02-deploy-elis-github-agent	MERGED	2026-05-07T10:33:56Z
419	PM-CHORE-90: close PE-OPS-FIXED-WORKSPACES-01	chore/pm-chore-90-close-pe-ops-fixed-workspaces-01	MERGED	2026-05-07T09:39:03Z
418	PE-OPS-FIXED-WORKSPACES-01: add fixed workspace governance	feature/pe-ops-fixed-workspaces-01-adopt-fixed-agent-workspace-and-github-write-boundary-model	MERGED	2026-05-07T08:51:58Z
417	PM-CHORE-89: open PE-OPS-FIXED-WORKSPACES-01	feature/pe-ops-fixed-workspaces-01-adopt-fixed-agent-workspace-and-github-write-boundary-model	MERGED	2026-05-06T22:02:55Z
416	PM-CHORE-88: open PE-GOV-RISK-TIER-01	feature/pe-gov-risk-tier-01-add-risk-tiered-pe-protocol	MERGED	2026-05-06T17:32:58Z

### gh api branches/main
{"name":"main","commit":{"sha":"340237a0aeb2f69a8fed170e15e36c8f4081b49a","node_id":"C_kwDOPi5jJNoAKDM0MDIzN2EwYWViMmY2OWE4ZmVkMTcwZTE1ZTM2YzhmNDA4MWI0OWE","commit":{"author":{"name":"Claude Code","email":"claude@electoralintegrity.org","date":"2026-05-07T17:35:02Z"},"committer":{"name":"Claude Code","email":"claude@electoralintegrity.org","date":"2026-05-07T17:35:57Z"},"message":"Add PM fixed workspace restoration procedure to governance pack","tree":{"sha":"85dc1543a9dc9b842bb67c901e2ccdd1b0e293e0","url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/git/trees/85dc1543a9dc9b842bb67c901e2ccdd1b0e293e0"},"url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/git/commits/340237a0aeb2f69a8fed170e15e36c8f4081b49a","comment_count":0,"verification":{"verified":false,"reason":"unsigned","signature":null,"payload":null,"verified_at":null}},"url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/commits/340237a0aeb2f69a8fed170e15e36c8f4081b49a","html_url":"https://github.com/rochasamurai/ELIS-Multi-AI-Agent-Platform/commit/340237a0aeb2f69a8fed170e15e36c8f4081b49a","comments_url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/commits/340237a0aeb2f69a8fed170e15e36c8f4081b49a/comments","author":null,"committer":null,"parents":[{"sha":"629d4e629b409235f2bba5aa6b97bfa371e298b7","url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/commits/629d4e629b409235f2bba5aa6b97bfa371e298b7","html_url":"https://github.com/rochasamurai/ELIS-Multi-AI-Agent-Platform/commit/629d4e629b409235f2bba5aa6b97bfa371e298b7"}]},"_links":{"self":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/branches/main","html":"https://github.com/rochasamurai/ELIS-Multi-AI-Agent-Platform/tree/main"},"protected":true,"protection":{"enabled":true,"required_status_checks":{"enforcement_level":"non_admins","contexts":["quality","tests","validate","current-pe-check","secrets-scope-check","review-evidence-check","slr-quality-check"],"checks":[{"context":"quality","app_id":15368},{"context":"tests","app_id":15368},{"context":"validate","app_id":15368},{"context":"current-pe-check","app_id":15368},{"context":"secrets-scope-check","app_id":15368},{"context":"review-evidence-check","app_id":15368},{"context":"slr-quality-check","app_id":15368}]}},"protection_url":"https://api.github.com/repos/rochasamurai/ELIS-Multi-AI-Agent-Platform/branches/main/protection"}
### gh run list
completed	failure	PM Observability Dashboard	PM Observability Dashboard	main	schedule	25515582296	11s	2026-05-07T18:50:15Z
completed	skipped	Notify PM Agent	Notify PM Agent	main	workflow_run	25512260095	1s	2026-05-07T17:41:35Z
completed	skipped	Auto-assign Validator	Auto-assign Validator	main	workflow_run	25512256542	1s	2026-05-07T17:41:31Z
completed	success	ELIS - Agent AutoMerge	ELIS - Agent AutoMerge	main	workflow_run	25512256518	15s	2026-05-07T17:41:31Z
completed	success	Add PM fixed workspace restoration procedure to governance pack	ELIS - CI	main	push	25512188585	1m21s	2026-05-07T17:40:07Z

## Notes
- no push, PR create, merge, metadata edits, settings changes, or secret/token changes were attempted
