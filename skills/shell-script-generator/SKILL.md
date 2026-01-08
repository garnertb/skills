---
name: shell-script-generator
description: Generate clean shell scripts following best practices.
metadata:
  author: garnertb
  version: "1.0"
---

# Shell Script Creator Skill

Generate clean shell scripts following best practices.See
[the reference guide](references/REFERENCE.md) for details.

## General guidelines

- Start scripts with shebang: (eg: `#!/bin/bash`)
- Fail fast, use `set -eo pipefail` (or `set -o errexit`) to cause the script to
  exit when a command fails.
  - Use `|| true` on programs that you intentionally let exit non-zero.
  - Note that ignoring an exit status with `|| true` is not a good practice,
    though it can be used in test scripts, if necessary.
- Set the exit code of a pipeline to that of the rightmost command that failed
- Disallow unset variables
- Usually use all three protections `set -o errexit -o nounset -o pipefail`
  - Use of `nounset` does require some extra code to either explicitly define
    variables (e.g. `FOO=`) or provide a default value, which may be blank:
    (e.g. `${FOO:-}`).
- avoid manually checking exit status with `$?`
- Always double quote variables, including subshells. No naked `$` signs
- Use Bash variable substitution if possible before awk/sed.
- Generally use double quotes unless it makes more sense to use single quotes.
- For simple conditionals, try using `&&` and `||`.
- Don't be afraid of `printf`, it's more powerful than `echo`.
- Put `then`, `do`, etc on same line, not newline.
- Skip `[[ ... ]]` in your if-expression if you can test for exit code instead.
- Use `.sh` or `.bash` extension if file is meant to be included/sourced. Never
  on executable script.
- Put complex one-liners of `sed`, `perl`, etc in a standalone function with a
  descriptive name.
- Good idea to include `[[ "$TRACE" ]] && set -x`
- Design for simplicity and obvious usage.
  - Avoid option flags and parsing, try optional environment variables instead.
  - Use subcommands for necessary different "modes".
- In large systems or for any CLI commands, add a description to functions.
  - Use `declare desc="description"` at the top of functions, even above
    argument declaration.
  - This can be queried/extracted using reflection. For example:
  ```
  eval $(type FUNCTION_NAME | grep 'declare desc=') && echo "$desc"
  ```
- Be conscious of the need for portability. Bash to run in a container can make
  more assumptions than Bash made to run on multiple platforms.
- When expecting or exporting environment, consider namespacing variables when
  subshells may be involved.
- Use hard tabs. Heredocs ignore leading tabs, allowing better indentation.
- `source` all dependencies before setting the `-e` or `+e` flags.
- ensure scripts support both mac and linux environments
