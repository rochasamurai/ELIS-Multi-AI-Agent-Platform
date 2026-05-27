# Evidence — ELIS GitHub Linux User Isolation

PE: PE-OPS-GITHUB-02

## Verified controls

- Linux user: elis-github
- GitHub identity through launcher: elis-git-bot
- GitHub repository permission: WRITE
- Non-interactive sudo: denied
- Own workspace write: PASS
- PM workspace write: PASS_DENIED
- Canonical repo write: PASS_DENIED

## Paths

- GitHub Agent workspace: /opt/elis/agent-worktrees/github-agent
- GitHub Agent launcher: /opt/elis/agent-worktrees/github-agent/bin/gh-agent
- Credential file: /opt/elis/secrets/github-agent.env
- Canonical repo: /opt/elis/repo

## Result

PASS: GitHub Agent can operate as elis-github / elis-git-bot and cannot write to PM workspace or canonical repo checkout.
