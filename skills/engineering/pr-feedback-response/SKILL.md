---
name: pr-feedback-response
description:
  Systematically address PR review feedback with thorough triage, planning, and
  implementation. Use when responding to PR comments, addressing review
  feedback, or processing code review suggestions. Triggers on "address PR
  feedback", "respond to review comments", "handle PR suggestions", or when
  working through unresolved PR review threads.
---

# PR Feedback Response

Structured workflow for holistically addressing PR review feedback with proper
triage, planning, and tracked implementation.

## Workflow Overview

1. **Fetch & Triage** - Gather all unresolved comments, assess each for
   actionability
2. **Plan** - Enter plan mode, draft approach for each feedback item
3. **Review Plan** - Consult principal-engineer-review skill to validate
   approach
4. **Present & Decide** - Show summary to user, get decisions on declined items
5. **Implement** - Execute plan with logical commit grouping

## Step 1: Fetch & Triage Feedback

### Fetch All Unresolved Comments

Use GitHub MCP tools to get complete PR context:

```
1. pull_request_read (method: get, perPage: 100)
   → Get PR description, extract linked issue numbers (e.g., "Fixes #123", "Closes #456")

2. pull_request_read (method: get_review_comments, perPage: 100)
   → Filter for threads where isResolved === false

3. pull_request_read (method: get_reviews, perPage: 100)
   → Capture formal review feedback (REQUEST_CHANGES especially)

4. pull_request_read (method: get_comments, perPage: 100)
   → General PR conversation that may contain actionable feedback

5. For each linked issue:
   issue_read (method: get) → Get issue context, requirements, acceptance criteria
   issue_read (method: get_comments) → Get discussion that may inform feedback triage
```

### Related Issues Context

Document linked issues in the plan to inform triage decisions:

```markdown
### Related Issues

- **#123**: [Issue title] - [Brief summary of requirements/acceptance criteria]
- **#456**: [Issue title] - [Brief summary]
```

Use issue context to assess whether feedback aligns with original requirements
or represents scope creep.

### Triage Each Comment

For each piece of feedback, determine disposition:

| Disposition                         | Criteria                          | Action                 |
| ----------------------------------- | --------------------------------- | ---------------------- |
| **Accept**                          | Valid, actionable, in-scope       | Plan implementation    |
| **Decline - Out of Scope**          | Valid but beyond PR intent        | Document reasoning     |
| **Decline - Cost/Complexity**       | Disproportionate effort for value | Document reasoning     |
| **Decline - Technically Incorrect** | Suggestion is wrong or harmful    | Document reasoning     |
| **Clarification Needed**            | Ambiguous or unclear request      | Note for user decision |

### Triage Output Format

For each comment, document:

```markdown
### Comment #N: [Brief summary]

- **Author**: @username
- **Location**: file.ts:42 (or "general" for PR comments)
- **Quote**: "[First 100 chars of comment]..."
- **Disposition**: Accept | Decline | Clarify
- **Reasoning**: [Why this disposition]
- **Recommended Response**: [If declined, suggested reply text]
```

## Step 2: Plan Implementation

Enter plan mode and create structured plan in session workspace.

### Plan Structure

```markdown
# PR Feedback Response Plan

## PR Context

- PR #: [number]
- Title: [title]
- Total Feedback Items: [N]
- Accepted: [N] | Declined: [N] | Needs Clarification: [N]

## Feedback Triage

### Accepted Items

[List each with brief implementation approach]

### Declined Items

[List each with reasoning and recommended response]

### Items Needing Clarification

[List with specific questions for user]

## Implementation Plan

### Commit Strategy

[Group related changes into logical commits]

### Commit 1: [Description]

- Addresses: Comment #N, #M (if related)
- Files: [list]
- Changes: [brief description]

### Commit 2: [Description]

...

## Risks & Considerations

[Any technical debt, edge cases, or concerns]
```

### Commit Grouping Rules

- **Cross-related feedback** → Group into single logical commit
- **Independent feedback** → Separate commit per feedback item
- Each commit message MUST reference the feedback it addresses

## Step 3: Consult Principal Engineer Review

After drafting the plan, invoke the `principal-engineer-review` skill:

> "Review this PR feedback response plan. Assess:
>
> 1. Are any declined items incorrectly triaged?
> 2. Are implementation approaches sound?
> 3. Is the commit grouping logical?
> 4. Any risks or edge cases missed?"

Iterate on plan based on principal engineer feedback until validated.

## Step 4: Present Summary & Get User Decisions

Present a concise summary to user:

```markdown
## PR Feedback Summary

**Accepted** (N items): [Brief list]

**Declined** (N items): For each declined item, show:

- Comment summary
- Reasoning
- Recommended response
- [Ask: Create reply comment? Y/N]

**Needs Clarification** (N items): [Show ambiguous items, ask for direction]

Ready to implement? [Confirm or modify plan]
```

Use `ask_user` tool for:

- Each declined item: whether to post a reply comment
- Any clarification items: what direction to take
- Final confirmation before implementation

## Step 5: Implement Plan

### Implementation Checklist

- [ ] Make changes per commit plan
- [ ] Run relevant tests/linting
- [ ] Create commits with messages referencing feedback
- [ ] Post reply comments for declined items (if user approved)
- [ ] Verify all accepted feedback is addressed

### Commit Message Format

```
Address PR feedback: [brief description]

Addresses feedback from @[author]:
- [Summary of comment]

[Additional context if needed]
```

### Reply Comment Format (for declined items)

```
Thanks for the feedback! After consideration:

[Reasoning for not implementing]

[If applicable: "This could be addressed in a follow-up PR/issue."]
```

## Error Handling

- **Cannot fetch PR data**: Verify PR number and repository access
- **Conflicting feedback**: Flag for user decision, do not assume
- **Implementation failures**: Roll back, document issue, ask for guidance
