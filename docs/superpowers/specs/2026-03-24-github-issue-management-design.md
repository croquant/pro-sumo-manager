# GitHub Issue Management System

## Overview

A structured project management system for Pro Sumo Manager using GitHub Issues, Projects, and Milestones. Organizes work in an Epic > Story > Task hierarchy with consistent templates, labels, and conventions.

## Goals

- Provide clear, structured tracking of all project work
- Enforce consistency across issues with templates
- Enable milestone-based release planning
- Make priorities and scope visible at a glance

## Milestones

Four near-term milestones representing shippable increments:

| Milestone | Description |
|-----------|-------------|
| v0.1 — Playable Onboarding | Complete setup flow: account creation, heya naming, initial roster draft |
| v0.2 — First Tournament | Enter a tournament, simulate bouts day-by-day, view results |
| v0.3 — Training & Progression | Between-tournament training, stat growth, wrestler development |
| v0.4 — Full Game Loop | Multiple tournaments, ranking changes, career progression, end-to-end playable |

## Issue Templates

Four GitHub issue templates in `.github/ISSUE_TEMPLATE/`:

### Epic

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

### Story

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

### Task

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

### Bug

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

## Labels

| Category | Label | Color | Description |
|----------|-------|-------|-------------|
| Type | `epic` | `#6E40C9` | Large feature area |
| Type | `story` | `#1D76DB` | User-facing behavior |
| Type | `task` | `#0E8A16` | Technical implementation unit |
| Type | `bug` | `#D73A4A` | Defect or unexpected behavior |
| Priority | `P0-critical` | `#B60205` | Must fix immediately |
| Priority | `P1-high` | `#D93F0B` | Important, address this milestone |
| Priority | `P2-medium` | `#FBCA04` | Normal priority |
| Priority | `P3-low` | `#C5DEF5` | Nice to have |
| Area | `frontend` | `#BFD4F2` | Templates, HTMX, CSS |
| Area | `backend` | `#D4C5F9` | Models, views, APIs |
| Area | `gameplay` | `#F9D0C4` | Game logic, services |
| Area | `infra` | `#C2E0C6` | CI, config, deployment |
| Area | `testing` | `#FEF2C0` | Test coverage, test tooling |
| Points | `SP:1` | `#EDEDED` | 1 story point |
| Points | `SP:2` | `#EDEDED` | 2 story points |
| Points | `SP:3` | `#EDEDED` | 3 story points |
| Points | `SP:5` | `#EDEDED` | 5 story points |
| Points | `SP:8` | `#EDEDED` | 8 story points |

## GitHub Project Board

A single GitHub Project (v2) named "Pro Sumo Manager" with columns:

| Column | Purpose |
|--------|---------|
| Backlog | Triaged but not yet scheduled |
| Ready | Has acceptance criteria, points assigned, ready to pick up |
| In Progress | Actively being worked on |
| In Review | PR open, awaiting review |
| Done | Merged and verified |

## Template Configuration

A `.github/ISSUE_TEMPLATE/config.yml` disables blank issues to enforce template usage:

```yaml
blank_issues_enabled: false
```

## Conventions

### Hierarchy and Lifecycle

- Epics stay open until all child stories are complete
- Epics are tracking issues — they do not move through board columns
- Stories must have acceptance criteria and an `SP:*` label before moving to "Ready"
- Tasks are optional — only create them when a story needs further decomposition
- Tasks are "Ready" when they have a definition of done and their parent story is in Ready or In Progress

### Story Points

- Only stories receive story points, applied via `SP:*` labels (not tracked elsewhere)
- Fibonacci scale (1, 2, 3, 5, 8) — anything above 8 must be split into smaller stories
- Tasks and bugs are not pointed

### Priority

- All stories and tasks should have a priority label (`P0` through `P3`)
- Bugs must have both a severity (in the template) and a priority label before entering the board

### Bugs

- Bugs are assigned to the milestone in which they will be fixed
- Bugs are "Ready" when triaged with severity and priority labels
- Use the optional "Related Issue" field to link bugs to their parent story or epic

### PRs and Branches

- Branch names follow the pattern: `<issue-number>-short-description` (e.g., `42-add-wrestler-draft-ui`)
- PRs use `Closes #N` or `Fixes #N` to auto-close issues on merge
- Each PR references its story/task number in the description

### Scope

- Only create detailed issues for the current milestone; future milestones stay high-level until they become active
