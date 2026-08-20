# No-argument routing: the context-aware menu

Read this when the user invokes `/dependabot` with no argument. They are asking
"what should I do?" Make the menu context-aware instead of static.

Lead the menu with `/dependabot report` as the top recommendation (one line on
why) and still show the rest below; don't silently jump into init. **Never
auto-run a command; the recommendation is a suggestion the user confirms.**

If the user's request is clearly about creating or improving
`.github/dependabot.yml` itself (adding an ecosystem, cutting PR noise, tuning
schedules, security-update grouping, etc.) rather than triaging existing
alerts/PRs, recommend `/dependabot config` instead of `report`.
