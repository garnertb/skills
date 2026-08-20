#!/bin/bash
#/ Usage: report.sh [--include-closed] <owner/repo> [owner/repo ...]
#/
#/ Gather repo metadata (archived/fork/private, default branch, languages),
#/ Dependabot security alerts, Dependabot PRs, and the dependabot.yml
#/ configuration for one or more repos, and print a JSON report to stdout.
#/ By default only open alerts and open PRs are fetched in full; pass
#/ --include-closed to also fetch closed/fixed/dismissed alerts and
#/ closed/merged PRs, rolled up into a closed_summary (counts by state and by
#/ dependency) to cut down on noise.
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

# Repo context that changes how alerts/PRs should be interpreted: archived and
# fork repos often don't get Dependabot updates, private repos need GHAS for
# alerts, and the language list flags ecosystems missing from dependabot.yml.
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
		'{repo: ($repo_info // {name_with_owner: $repo}), alerts: $alerts, pull_requests: $prs, dependabot_config: $config}'
}

for repo in "$@"; do
	report_for_repo "${repo}" "${include_closed}"
done | jq -s '.'
