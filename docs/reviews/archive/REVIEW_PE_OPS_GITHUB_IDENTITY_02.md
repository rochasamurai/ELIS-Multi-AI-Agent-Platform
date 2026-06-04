# REVIEW — PE-OPS-GITHUB-IDENTITY-02 (Gate 2)

**Reviewer:** infra-val-b  
**Date:** 2026-06-04  
**Branch:** feature/pe-ops-github-identity-02-gate2-host-runtime-a2a-mailbox  
**Commit:** 26485ea5  
**Implementer:** infra-impl-a  

---

### Verdict

PASS

### Gate results

V1 PASS: Branch base — merge-base `b4ecc0a12aad575eca5430c770bdf1c6e0583622` matches origin/main HEAD.

V2 PASS: HANDOFF.md exists and committed — sole file in commit 26485ea5; content verified via `git show HEAD:HANDOFF.md`.

V3 PASS: github-agent git identity — `user.name = elis-git-bot`, `user.email = elis-git-bot@electoralintegrity.org`, source: `file:/opt/elis/repo/.git/worktrees/github-agent/config.worktree` (linked worktree).

V4 PASS: config.worktree backup exists — path: `/opt/elis/repo/.git/worktrees/github-agent/config.worktree.bak-pe-ops-github-identity-02`, owner: samurai, size: 73 bytes.

V5 PASS: A2A mailbox directories — `inbox/`, `processed/`, `dead/` all exist; owner: samurai:samurai; mode: 0750 (drwxr-x---).

V6 PASS: Secret boundary — validator (running as `samurai`, uid 1000) cannot stat `/opt/elis/secrets/github-agent.env` because parent directory is owned by `root:elis-github-secrets` mode 0750, and `samurai` is not a member of group `elis-github-secrets`. This is exactly the expected behaviour — the secret boundary restricts access to the `elis-github` service user only. The directory exists and has correct restrictive permissions. Independent file-existence confirmation is not possible from the validator role; this is acceptable as it proves the boundary is enforced.

V7 PASS: bin/gh-agent located but not executed — primary path: `/opt/elis/agent-worktrees/github-agent/bin/gh-agent`; file found, executable, not executed during validation.

V8 PASS: No secret content in HANDOFF.md — `grep -i` matched only structural references (group name `elis-github-secrets`, directory path `/opt/elis/secrets/`, section heading `Secret boundary check`). No token values, passwords, PAT strings, GHP_/GHS_ prefixes, or credential content found.

V9 PASS: Scope gate — only `HANDOFF.md` changed on the PE branch relative to origin/main.

### Scope

Gate 2 — host-runtime git identity and A2A mailbox

### Required fixes

None

### Evidence

#### V1 — Branch base

```bash
$ git log --oneline -3
26485ea5 feat(PE-OPS-GITHUB-IDENTITY-02): Gate 2 implementation — host-runtime identity and A2A mailbox
b4ecc0a1 chore(PM-CHORE-119): open PE-OPS-GITHUB-IDENTITY-02 — Gate 2 host-runtime identity + A2A mailbox
2a0f3e84 chore(PM-CHORE-118): close PE-OPS-GITHUB-IDENTITY-01 Gate 1 — mark merged, restore plan-complete mode

$ git merge-base HEAD origin/main
b4ecc0a12aad575eca5430c770bdf1c6e0583622
```

#### V2 — HANDOFF.md committed

```bash
$ git show HEAD --stat
commit 26485ea50c7cfffdc1878ae0e9e45e2736c9730f
Author: infra-impl-a <infra-impl-a@openclaw.local>
Date:   Thu Jun 4 17:57:29 2026 +0100

    feat(PE-OPS-GITHUB-IDENTITY-02): Gate 2 implementation — host-runtime identity and A2A mailbox

 HANDOFF.md | 244 +++++++++++++++++++++++++++++++++----------------------------
 1 file changed, 132 insertions(+), 112 deletions(-)

$ git show HEAD:HANDOFF.md | head -30
# PE-OPS-GITHUB-IDENTITY-02 Gate 2 Implementation Report

## Status Packet

### Implementer
infra-impl-a

### Branch
feature/pe-ops-github-identity-02-gate2-host-runtime-a2a-mailbox

### Evidence

#### G2-S1: Verify OS user elis-github exists
...
```

#### V3 — Git identity

```bash
$ git -C /opt/elis/agent-worktrees/github-agent config --local user.name
elis-git-bot
$ git -C /opt/elis/agent-worktrees/github-agent config --local user.email
elis-git-bot@electoralintegrity.org
$ git -C /opt/elis/agent-worktrees/github-agent config --show-origin user.name
file:/opt/elis/repo/.git/worktrees/github-agent/config.worktree	elis-git-bot
$ git -C /opt/elis/agent-worktrees/github-agent config --show-origin user.email
file:/opt/elis/repo/.git/worktrees/github-agent/config.worktree	elis-git-bot@electoralintegrity.org
```

#### V4 — config.worktree backup

```bash
$ ls -la /opt/elis/repo/.git/worktrees/github-agent/config.worktree.bak-pe-ops-github-identity-02
-rw-rw-r-- 1 samurai samurai 73 Jun  4 17:57 /opt/elis/repo/.git/worktrees/github-agent/config.worktree.bak-pe-ops-github-identity-02
```

#### V5 — A2A mailbox directories

```bash
$ ls -la /opt/elis/a2a/mailboxes/github-agent/
total 20
drwxr-x---  5 samurai samurai 4096 Jun  4 17:49 .
drwxr-x--- 10 samurai samurai 4096 Jun  4 17:49 ..
drwxr-x---  2 samurai samurai 4096 Jun  4 17:49 dead
drwxr-x---  2 samurai samurai 4096 Jun  4 17:49 inbox
drwxr-x---  2 samurai samurai 4096 Jun  4 17:49 processed

$ stat /opt/elis/a2a/mailboxes/github-agent/inbox
  File: /opt/elis/a2a/mailboxes/github-agent/inbox
  Size: 4096      	Blocks: 8          IO Block: 4096   directory
Device: 259,1	Inode: 8430419     Links: 2
Access: (0750/drwxr-x---)  Uid: ( 1000/ samurai)   Gid: ( 1000/ samurai)
Access: 2026-06-04 17:51:16.919737131 +0100
Modify: 2026-06-04 17:49:13.750074029 +0100
Change: 2026-06-04 17:49:20.629242989 +0100
 Birth: 2026-06-04 17:49:13.750074029 +0100

$ stat /opt/elis/a2a/mailboxes/github-agent/processed
  File: /opt/elis/a2a/mailboxes/github-agent/processed
  Size: 4096      	Blocks: 8          IO Block: 4096   directory
Device: 259,1	Inode: 8430420     Links: 2
Access: (0750/drwxr-x---)  Uid: ( 1000/ samurai)   Gid: ( 1000/ samurai)
Access: 2026-06-04 17:51:16.919737131 +0100
Modify: 2026-06-04 17:49:13.750074029 +0100
Change: 2026-06-04 17:49:20.629242989 +0100
 Birth: 2026-06-04 17:49:13.750074029 +0100

$ stat /opt/elis/a2a/mailboxes/github-agent/dead
  File: /opt/elis/a2a/mailboxes/github-agent/dead
  Size: 4096      	Blocks: 8          IO Block: 4096   directory
Device: 259,1	Inode: 8430421     Links: 2
Access: (0750/drwxr-x---)  Uid: ( 1000/ samurai)   Gid: ( 1000/ samurai)
Access: 2026-06-04 17:51:16.919737131 +0100
Modify: 2026-06-04 17:49:13.750074029 +0100
Change: 2026-06-04 17:49:20.629242989 +0100
 Birth: 2026-06-04 17:49:13.750074029 +0100
```

#### V6 — Secret boundary

```bash
$ stat /opt/elis/secrets/github-agent.env
stat: cannot statx '/opt/elis/secrets/github-agent.env': Permission denied

$ stat /opt/elis/secrets
  File: /opt/elis/secrets
  Size: 4096      	Blocks: 8          IO Block: 4096   directory
Device: 259,1	Inode: 8817007     Links: 2
Access: (0750/drwxr-x---)  Uid: (    0/    root)   Gid: ( 982/elis-github-secrets)
Access: 2026-05-08 11:57:18.497457745 +0100
Modify: 2026-05-27 16:29:14.192061996 +0100
Change: 2026-05-27 16:29:14.192061996 +0100
 Birth: 2026-05-07 19:39:23.576725442 +0100

$ id
uid=1000(samurai) gid=1000(samurai) groups=1000(samurai),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),114(lpadmin),124(docker),984(ollama)

$ getent group elis-github-secrets
elis-github-secrets:x:982:elis-github
```

Validator is not a member of `elis-github-secrets`; permission denial confirms the boundary is correctly enforced.

#### V7 — bin/gh-agent

```bash
$ find /opt/elis -path '*/bin/gh-agent' -type f -executable -print
/opt/elis/repo/bin/gh-agent
/opt/elis/agent-worktrees/infra-val-b/bin/gh-agent
/opt/elis/agent-worktrees/github-agent.invalid-clone-backup.20260527T2006Z/bin/gh-agent
/opt/elis/agent-worktrees/infra-impl-b/bin/gh-agent
/opt/elis/agent-worktrees/github-agent.linked-backup.20260508T141916/bin/gh-agent
/opt/elis/agent-worktrees/github-agent/bin/gh-agent
/opt/elis/agent-worktrees/PE-OPS-GITHUB-AGENT-PRODUCTION-01-infra-impl-b/bin/gh-agent
/opt/elis/agent-worktrees/infra-impl-a/bin/gh-agent
/opt/elis/agent-worktrees/pm/bin/gh-agent
/opt/elis/agent-worktrees/infra-val-a/bin/gh-agent

$ ls -la /opt/elis/agent-worktrees/github-agent/bin/gh-agent
-rwxrwxr-x 1 samurai elis-github 9235 May 27 21:07 /opt/elis/agent-worktrees/github-agent/bin/gh-agent
```

Not executed during validation.

#### V8 — No secret content in HANDOFF.md

```bash
$ grep -i 'token\|secret\|password\|key\|credential\|pat\|ghp_\|ghs_' /opt/elis/agent-worktrees/infra-impl-a/HANDOFF.md
uid=995(elis-github) gid=983(elis-github) groups=983(elis-github),982(elis-github-secrets)
$ find /opt/elis -path '*/bin/gh-agent' -type f -executable -print
#### G2-S13: Secret boundary check
$ stat /opt/elis/secrets/github-agent.env
stat: cannot statx '/opt/elis/secrets/github-agent.env': Permission denied
```

Matches are structural references only (group name, directory path, section heading). No credential values leaked.

#### V9 — Scope gate

```bash
$ git diff origin/main..HEAD --name-only
HANDOFF.md
```

Only HANDOFF.md changed — scope gate clean.
