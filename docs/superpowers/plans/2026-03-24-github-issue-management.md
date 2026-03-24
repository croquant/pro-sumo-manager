# GitHub Issue Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up GitHub issue templates, labels, milestones, and a project board to enable structured Epic > Story > Task project management.

**Architecture:** File-based issue templates in `.github/ISSUE_TEMPLATE/`, GitHub API calls via `gh` CLI for labels/milestones/project board. No application code changes.

**Tech Stack:** GitHub Issue Forms (YAML), `gh` CLI

**Spec:** `docs/superpowers/specs/2026-03-24-github-issue-management-design.md`

---

## File Structure

```
.github/ISSUE_TEMPLATE/
  config.yml       # Disables blank issues
  epic.yml         # Epic template
  story.yml        # Story template
  task.yml         # Task template
  bug.yml          # Bug template (overwrites default if exists)
```

No test files — this plan is entirely configuration and GitHub API setup.

---

### Task 1: Create Issue Template Directory and Config

**Files:**
- Create: `.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1: Create config.yml**

```yaml
blank_issues_enabled: false
```

Write this file to `.github/ISSUE_TEMPLATE/config.yml`.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/config.yml
git commit -m "chore: add issue template config, disable blank issues"
```

---

### Task 2: Create Epic Issue Template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/epic.yml`

- [ ] **Step 1: Create epic.yml**

```yaml
name: Epic
description: A large feature area grouping multiple stories
labels: ["epic"]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What system or feature area does this epic cover?
    validations:
      required: true
  - type: textarea
    id: goals
    attributes:
      label: Goals
      description: What does success look like for this epic?
    validations:
      required: true
  - type: textarea
    id: stories
    attributes:
      label: Stories
      description: Checklist of child stories (link as they are created)
      value: |
        - [ ] #
    validations:
      required: false
```

Write this file to `.github/ISSUE_TEMPLATE/epic.yml`.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/epic.yml
git commit -m "chore: add epic issue template"
```

---

### Task 3: Create Story Issue Template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/story.yml`

- [ ] **Step 1: Create story.yml**

```yaml
name: Story
description: A user-facing behavior or capability
labels: ["story"]
body:
  - type: input
    id: parent-epic
    attributes:
      label: Parent Epic
      description: "Link to the parent epic (e.g., #42)"
    validations:
      required: true
  - type: textarea
    id: user-story
    attributes:
      label: User Story
      description: "As a [role], I want to [action] so that [benefit]"
    validations:
      required: true
  - type: textarea
    id: acceptance-criteria
    attributes:
      label: Acceptance Criteria
      description: Checklist of conditions that must be true for this story to be complete
      value: |
        - [ ]
    validations:
      required: true
  - type: textarea
    id: design-notes
    attributes:
      label: Design Notes
      description: Optional UI/UX considerations, mockups, or references
    validations:
      required: false
```

Write this file to `.github/ISSUE_TEMPLATE/story.yml`.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/story.yml
git commit -m "chore: add story issue template"
```

---

### Task 4: Create Task Issue Template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/task.yml`

- [ ] **Step 1: Create task.yml**

```yaml
name: Task
description: A technical implementation unit within a story
labels: ["task"]
body:
  - type: input
    id: parent-story
    attributes:
      label: Parent Story
      description: "Link to the parent story (e.g., #45)"
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Description
      description: Technical implementation details
    validations:
      required: true
  - type: textarea
    id: scope
    attributes:
      label: Scope
      description: Files, services, or modules likely affected
    validations:
      required: true
  - type: textarea
    id: definition-of-done
    attributes:
      label: Definition of Done
      description: What must be true for this task to be complete?
      value: |
        - [ ]
    validations:
      required: true
```

Write this file to `.github/ISSUE_TEMPLATE/task.yml`.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/task.yml
git commit -m "chore: add task issue template"
```

---

### Task 5: Create Bug Issue Template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug.yml`

Note: A default `bug` label already exists on the repo. The template references it, so no extra label creation needed for the bug type.

- [ ] **Step 1: Create bug.yml**

```yaml
name: Bug
description: A defect or unexpected behavior
labels: ["bug"]
body:
  - type: input
    id: related-issue
    attributes:
      label: Related Issue
      description: "Link to related story or epic, if any (e.g., #45)"
    validations:
      required: false
  - type: textarea
    id: steps-to-reproduce
    attributes:
      label: Steps to Reproduce
      description: Minimal steps to trigger the bug
      value: |
        1.
        2.
        3.
    validations:
      required: true
  - type: textarea
    id: expected-behavior
    attributes:
      label: Expected Behavior
      description: What should happen?
    validations:
      required: true
  - type: textarea
    id: actual-behavior
    attributes:
      label: Actual Behavior
      description: What actually happens?
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Browser, OS, Python version, or other relevant details
    validations:
      required: false
  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - Critical
        - Major
        - Minor
    validations:
      required: true
```

Write this file to `.github/ISSUE_TEMPLATE/bug.yml`.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/bug.yml
git commit -m "chore: add bug issue template"
```

---

### Task 6: Clean Up Default Labels and Create New Labels

**Files:** None (GitHub API only)

The repo currently has these default labels that should be removed (they conflict with or are replaced by the new system): `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`, `codex`, `dependencies`, `python`, `python:uv`.

The `bug` label already exists and is used by the bug template — keep it but update its color to match the spec (`#D73A4A`).

- [ ] **Step 1: Delete unused default labels**

```bash
gh label delete "documentation" --yes
gh label delete "duplicate" --yes
gh label delete "enhancement" --yes
gh label delete "good first issue" --yes
gh label delete "help wanted" --yes
gh label delete "invalid" --yes
gh label delete "question" --yes
gh label delete "wontfix" --yes
gh label delete "codex" --yes
gh label delete "dependencies" --yes
gh label delete "python" --yes
gh label delete "python:uv" --yes
```

- [ ] **Step 2: Update existing bug label color**

```bash
gh label edit "bug" --color "D73A4A" --description "Defect or unexpected behavior"
```

- [ ] **Step 3: Create type labels**

```bash
gh label create "epic" --color "6E40C9" --description "Large feature area"
gh label create "story" --color "1D76DB" --description "User-facing behavior"
gh label create "task" --color "0E8A16" --description "Technical implementation unit"
```

- [ ] **Step 4: Create priority labels**

```bash
gh label create "P0-critical" --color "B60205" --description "Must fix immediately"
gh label create "P1-high" --color "D93F0B" --description "Important, address this milestone"
gh label create "P2-medium" --color "FBCA04" --description "Normal priority"
gh label create "P3-low" --color "C5DEF5" --description "Nice to have"
```

- [ ] **Step 5: Create area labels**

```bash
gh label create "frontend" --color "BFD4F2" --description "Templates, HTMX, CSS"
gh label create "backend" --color "D4C5F9" --description "Models, views, APIs"
gh label create "gameplay" --color "F9D0C4" --description "Game logic, services"
gh label create "infra" --color "C2E0C6" --description "CI, config, deployment"
gh label create "testing" --color "FEF2C0" --description "Test coverage, test tooling"
```

- [ ] **Step 6: Create story point labels**

```bash
gh label create "SP:1" --color "EDEDED" --description "1 story point"
gh label create "SP:2" --color "EDEDED" --description "2 story points"
gh label create "SP:3" --color "EDEDED" --description "3 story points"
gh label create "SP:5" --color "EDEDED" --description "5 story points"
gh label create "SP:8" --color "EDEDED" --description "8 story points"
```

- [ ] **Step 7: Verify labels**

```bash
gh label list
```

Expected: 18 labels total (4 type + 4 priority + 5 area + 5 points).

---

### Task 7: Create Milestones

**Files:** None (GitHub API only)

- [ ] **Step 1: Create all four milestones**

```bash
gh api repos/{owner}/{repo}/milestones -f title="v0.1 — Playable Onboarding" -f description="Complete setup flow: account creation, heya naming, initial roster draft"
gh api repos/{owner}/{repo}/milestones -f title="v0.2 — First Tournament" -f description="Enter a tournament, simulate bouts day-by-day, view results"
gh api repos/{owner}/{repo}/milestones -f title="v0.3 — Training & Progression" -f description="Between-tournament training, stat growth, wrestler development"
gh api repos/{owner}/{repo}/milestones -f title="v0.4 — Full Game Loop" -f description="Multiple tournaments, ranking changes, career progression, end-to-end playable"
```

- [ ] **Step 2: Verify milestones**

```bash
gh api repos/{owner}/{repo}/milestones --jq '.[].title'
```

Expected output:
```
v0.1 — Playable Onboarding
v0.2 — First Tournament
v0.3 — Training & Progression
v0.4 — Full Game Loop
```

---

### Task 8: Create GitHub Project Board

**Files:** None (GitHub API only)

- [ ] **Step 1: Create the project**

```bash
gh project create --owner @me --title "Pro Sumo Manager"
```

Note the project number from the output.

- [ ] **Step 2: Add status field columns**

GitHub Projects v2 come with a default "Status" field. Update it to have the 5 required columns. Use the `gh project field-list` and `gh project field-edit` commands, or the GraphQL API if needed:

```bash
# List project fields to find the Status field ID
gh project field-list <PROJECT_NUMBER> --owner @me

# The Status field needs these options: Backlog, Ready, In Progress, In Review, Done
# This may require the GraphQL API — use gh api graphql
```

If the CLI doesn't support editing single-select options directly, use the GitHub web UI to configure the Status field columns to: **Backlog, Ready, In Progress, In Review, Done**.

- [ ] **Step 3: Verify the project board**

Open the project in the browser to confirm columns are set up:

```bash
gh project view <PROJECT_NUMBER> --owner @me --web
```
