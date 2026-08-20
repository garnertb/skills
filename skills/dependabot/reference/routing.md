# No-argument routing: the context-aware menu

Read this when the user invokes `/dependabot` with no argument. They are asking
"what should I do?" Make the menu context-aware instead of static.

Lead the menu with `/dependabot report` as the top recommendation (one line on
why) and still show the rest below; don't silently jump into init. **Never
auto-run a command; the recommendation is a suggestion the user confirms.**
