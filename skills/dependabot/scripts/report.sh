#!/bin/bash
#/ Usage: report.sh [--include-closed] <owner/repo> [owner/repo ...]
#/
#/ Gather repo metadata (archived/fork/private, default branch, languages),
#/ Dependabot security alerts, Dependabot PRs, a manifest inventory of every
#/ ecosystem signature present in the file tree, and the dependabot.yml
#/ configuration for one or more repos, and print a JSON report to stdout.
#/ By default only open alerts and open PRs are fetched in full; pass
#/ --include-closed to also fetch closed/fixed/dismissed alerts and
#/ closed/merged PRs, rolled up into a closed_summary (counts by state and by
#/ dependency) to cut down on noise.
#/
#/ The manifest_inventory is SHA-pinned and fails closed: when complete is
#/ false, no ecosystem may be reported as absent.
#/
#/ Requires: gh (authenticated), jq
#/
#/ OPTIONS:
#/   -h | --help          Show this message.
#/   --include-closed     Also fetch and summarize closed alerts and PRs.
#/
#/ EXAMPLE:
#/   scripts/report.sh octocat/hello-world
#/   scripts/report.sh --include-closed octocat/hello-world > report.json

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	grep '^#/' <"$0" | cut -c 4-
	exit 2
fi

set -o errexit -o nounset -o pipefail

if [ "$#" -eq 0 ]; then
	grep '^#/' <"$0" | cut -c 4-
	exit 2
fi

include_closed=false
while [ "$#" -gt 0 ]; do
	case "$1" in
		--include-closed)
			include_closed=true
			shift
			;;
		--)
			shift
			break
			;;
		-*)
			echo "error: unknown option: $1" >&2
			exit 1
			;;
		*)
			break
			;;
	esac
done

if [ "$#" -eq 0 ]; then
	grep '^#/' <"$0" | cut -c 4-
	exit 2
fi

command -v gh >/dev/null || { echo "error: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "error: jq is required" >&2; exit 1; }

fetch_alerts() {
	declare repo="$1" include_closed="$2"
	declare state_filter="?state=open"
	[ "${include_closed}" = "true" ] && state_filter=""
	gh api "repos/${repo}/dependabot/alerts${state_filter}" --paginate 2>/dev/null \
		| jq --argjson include_closed "${include_closed}" '
			def alert_summary: {
				number,
				state,
				severity: .security_advisory.severity,
				summary: .security_advisory.summary,
				package: .dependency.package.name,
				ecosystem: .dependency.package.ecosystem,
				manifest_path: .dependency.manifest_path,
				html_url,
				created_at,
				fixed_at,
				auto_dismissed_at
			};
			{
				open: [.[] | select(.state == "open") | alert_summary],
				closed_summary: (
					if $include_closed then {
						total: [.[] | select(.state != "open")] | length,
						fixed: [.[] | select(.state == "fixed")] | length,
						dismissed: [.[] | select(.state == "dismissed" or .state == "auto_dismissed")] | length,
						by_package: (
							[.[] | select(.state != "open") | .dependency.package.name] as $names
							| ($names | unique) as $unique_names
							| [$unique_names[] as $name | {package: $name, count: ($names | map(select(. == $name)) | length)}]
							| sort_by(-.count)
						)
					} else null end
				)
			}' || echo '{"open":[],"closed_summary":null}'
}

fetch_prs() {
	declare repo="$1" include_closed="$2"
	declare state_filter="open"
	[ "${include_closed}" = "true" ] && state_filter="all"
	gh pr list --repo "${repo}" --app dependabot --state "${state_filter}" --limit 500 \
		--json number,title,url,state,headRefName,createdAt,closedAt,mergedAt,statusCheckRollup \
		| jq --argjson include_closed "${include_closed}" '
			def pr_summary: {
				number,
				title,
				url,
				state,
				branch: .headRefName,
				created_at: .createdAt,
				closed_at: .closedAt,
				ci_status: ([.statusCheckRollup[]?.conclusion // .statusCheckRollup[]?.state] | unique | join(","))
			};
			def dependency_name: (.title as $title | ($title | capture("^(?:build|chore)\\(deps(?:-dev)?\\): bump (?<pkg>\\S+)").pkg) // $title);
			{
				open: [.[] | select(.state == "OPEN") | pr_summary],
				closed_summary: (
					if $include_closed then {
						total: [.[] | select(.state != "OPEN")] | length,
						merged: [.[] | select(.state == "MERGED")] | length,
						closed_unmerged: [.[] | select(.state == "CLOSED")] | length,
						by_package: (
							[.[] | select(.state != "OPEN") | dependency_name] as $names
							| ($names | unique) as $unique_names
							| [$unique_names[] as $name | {package: $name, count: ($names | map(select(. == $name)) | length)}]
							| sort_by(-.count)
						)
					} else null end
				)
			}'
}

fetch_config() {
	declare repo="$1"
	declare content
	content="$(gh api "repos/${repo}/contents/.github/dependabot.yml" --jq '.content' 2>/dev/null | base64 --decode 2>/dev/null || true)"
	if [ -z "${content}" ]; then
		echo 'null'
	else
		jq -n --arg yaml "${content}" '{raw: $yaml}'
	fi
}

# Deterministic manifest inventory. The repo language list can't be used to find
# ecosystems: linguist reports languages, so it never surfaces Dev Containers,
# Actions, pre-commit, or submodules. This walks the actual file tree instead.
#
# Fails closed: any unresolved ref, API error, or truncated tree yields
# complete=false, and callers must not report an ecosystem as absent from an
# incomplete scan.
#
# The signature table below mirrors the ecosystem table in
# reference/dependabot-config.md; keep the two in sync.
fetch_manifests() {
	declare repo="$1"
	declare branch sha tree

	# gh writes the API error body to stdout on failure, so each capture is
	# gated on exit status rather than on the output being non-empty.
	if ! branch="$(gh api "repos/${repo}" --jq '.default_branch' 2>/dev/null)"; then
		branch=""
	fi
	if [ -z "${branch}" ] || [ "${branch}" = "null" ]; then
		jq -n '{complete: false, error: "could not resolve default branch (empty repo, not found, or no access)", ref: null, sha: null, entries: []}'
		return
	fi

	# Resolve to a commit SHA via a query param so branch names containing "/"
	# can't break the request path, and so every entry comes from one snapshot.
	if ! sha="$(gh api "repos/${repo}/commits?sha=${branch}&per_page=1" --jq '.[0].sha' 2>/dev/null)"; then
		sha=""
	fi
	if [ -z "${sha}" ] || [ "${sha}" = "null" ]; then
		jq -n --arg branch "${branch}" '{complete: false, error: "could not resolve a commit for the default branch", ref: $branch, sha: null, entries: []}'
		return
	fi

	if ! tree="$(gh api "repos/${repo}/git/trees/${sha}?recursive=1" 2>/dev/null)"; then
		tree=""
	fi
	if [ -z "${tree}" ]; then
		jq -n --arg branch "${branch}" --arg sha "${sha}" '{complete: false, error: "git trees request failed (rate limit, permission, or size)", ref: $branch, sha: $sha, entries: []}'
		return
	fi

	jq --arg branch "${branch}" --arg sha "${sha}" '
		def to_dir($parts): if ($parts | length) == 0 then "/" else "/" + ($parts | join("/")) end;

		# Dependabot resolves .devcontainer.json, .devcontainer/devcontainer.json,
		# and .devcontainer/<name>/devcontainer.json RELATIVE to `directory`, so
		# the project root is the path above .devcontainer -- never .devcontainer
		# itself.
		def devcontainer_root($parts):
			($parts | index(".devcontainer")) as $i
			| if $i == null then $parts[:-1] else $parts[:$i] end;

		def ecosystem_for($base):
			if $base | test("^(package\\.json|package-lock\\.json|pnpm-lock\\.yaml|yarn\\.lock)$") then "npm"
			elif $base | test("^(requirements.*\\.txt|Pipfile|setup\\.py)$") then "pip"
			elif $base == "uv.lock" then "uv"
			elif $base == "pyproject.toml" then "pip|uv"
			elif $base | test("^Dockerfile") then "docker"
			elif $base | test("^docker-compose.*\\.ya?ml$") then "docker-compose"
			elif $base == "go.mod" then "gomod"
			elif $base | test("^Gemfile$") then "bundler"
			elif $base == "Cargo.toml" then "cargo"
			elif $base == "composer.json" then "composer"
			elif $base | test("\\.csproj$|^packages\\.config$") then "nuget"
			elif $base == "global.json" then "dotnet-sdk"
			elif $base == "pom.xml" then "maven"
			elif $base | test("^build\\.gradle(\\.kts)?$") then "gradle"
			elif $base | test("\\.tf$") then "terraform|opentofu"
			elif $base == "Chart.yaml" then "helm"
			elif $base == "mix.exs" then "mix"
			elif $base == "Package.swift" then "swift"
			elif $base == "pubspec.yaml" then "pub"
			elif $base | test("^bun\\.lock(b)?$") then "bun"
			elif $base | test("^(\\.devcontainer\\.json|devcontainer\\.json)$") then "devcontainers"
			elif $base == ".gitmodules" then "gitsubmodule"
			elif $base | test("^\\.pre-commit-config\\.ya?ml$") then "pre-commit"
			else null end;

		.truncated as $truncated
		| [
			.tree[]
			| select(.type == "blob" or .type == "commit")
			| .path as $path
			| ($path | split("/")) as $parts
			| ($parts | last) as $base
			| (
				if .type == "commit" then "gitsubmodule"
				elif ($path | test("^\\.github/workflows/.*\\.ya?ml$")) then "github-actions"
				else ecosystem_for($base) end
			) as $eco
			| select($eco != null)
			| {
				path: $path,
				ecosystem: $eco,
				project_root: (
					if $eco == "devcontainers" then to_dir(devcontainer_root($parts))
					elif $eco == "github-actions" then "/"
					else to_dir($parts[:-1]) end
				),
				ambiguous: ($eco | test("\\|")),
				# Vendored, generated, and fixture trees produce real manifests that
				# usually should not be configured. Surface them, do not auto-adopt.
				candidate_only: ($path | test("(^|/)(node_modules|vendor|third_party|testdata|fixtures)/|(^|/)test/fixtures/"))
			}
		]
		| unique
		| {
			complete: ($truncated | not),
			error: (if $truncated then "git tree was truncated; scan is incomplete -- re-run against a local clone (git clone --filter=blob:none) before reporting any ecosystem as absent" else null end),
			ref: $branch,
			sha: $sha,
			entries: .
		}' <<<"${tree}" || jq -n '{complete: false, error: "failed to parse git tree response", ref: null, sha: null, entries: []}'
}

# Repo context that changes how alerts/PRs should be interpreted: archived and
# fork repos often don't get Dependabot updates, and private repos need GHAS for
# alerts. The language list is narrative context only -- ecosystem gaps come
# from manifest_inventory, since linguist cannot see non-language ecosystems.
fetch_repo() {
	declare repo="$1"
	gh repo view "${repo}" --json name,nameWithOwner,url,isArchived,isFork,isPrivate,visibility,defaultBranchRef,pushedAt,updatedAt,primaryLanguage,languages,isSecurityPolicyEnabled,securityPolicyUrl,owner,isInOrganization 2>/dev/null \
		| jq '{
			name,
			name_with_owner: .nameWithOwner,
			url,
			is_archived: .isArchived,
			is_fork: .isFork,
			is_private: .isPrivate,
			visibility,
			default_branch: .defaultBranchRef.name,
			pushed_at: .pushedAt,
			updated_at: .updatedAt,
			primary_language: .primaryLanguage.name,
			languages: [.languages[]?.node.name],
			is_security_policy_enabled: .isSecurityPolicyEnabled,
			security_policy_url: .securityPolicyUrl,
			owner: .owner.login,
			is_in_organization: .isInOrganization
		}' || echo 'null'
}

report_for_repo() {
	declare repo="$1" include_closed="$2"
	jq -n \
		--arg repo "${repo}" \
		--argjson repo_info "$(fetch_repo "${repo}")" \
		--argjson alerts "$(fetch_alerts "${repo}" "${include_closed}")" \
		--argjson prs "$(fetch_prs "${repo}" "${include_closed}")" \
		--argjson config "$(fetch_config "${repo}")" \
		--argjson manifests "$(fetch_manifests "${repo}")" \
		'{repo: ($repo_info // {name_with_owner: $repo}), alerts: $alerts, pull_requests: $prs, dependabot_config: $config, manifest_inventory: $manifests}'
}

for repo in "$@"; do
	report_for_repo "${repo}" "${include_closed}"
done | jq -s '.'
