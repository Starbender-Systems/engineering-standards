# GitHub repository setup

## When to use

Creating a GitHub repository or reviewing its initial settings, contribution process, branch protections, CI, and release boundaries.

## Preconditions

Read [general](../standards/general.md), [git](../standards/git.md), [security](../standards/security.md), [testing](../standards/testing.md), and [documentation](../standards/documentation.md). Confirm the intended organization, repository name, visibility, maintainers, and authorization for remote changes.

Repository administration access is needed for settings and protections; organization policies and GitHub plan availability can limit the choices. A successful content read does not establish administration access. Record unavailable settings and authorization failures rather than treating them as disabled features.

## Implementation steps

### 1. Record the configuration decisions

Use this table as a starting profile, then record the repository owner's choices in the repository's development/contribution guide. Adapt the proposals to the project's needs and established organization policies.

| Concern | Starting profile and decision |
| --- | --- |
| Identity | Select the actual organization, name, description, visibility, license, and intended maintainers. |
| Branches | Choose a single protected `main`, or a `development` integration branch plus stable `main`. A second branch is useful only when its promotion/release process is defined. |
| Default branch | Select the default branch explicitly; document when ordinary PRs target a different integration branch. |
| Contributions | Choose collaborator-only PRs or outside contributions, and make access settings agree with the contribution guide. |
| Merge method | Consider squash-only merging for concise history. Confirm the strategy also works for repeated integration-to-release promotions if using two long-lived branches. |
| Commit defaults | Prefer PR title and description for squash messages, with a meaningful PR summary. If using PR title and commit details instead, inspect the resulting body against the Git standard. |
| Reviews | Start with one approval, stale approval dismissal, code-owner review, and resolved conversations on each integration/release branch. Confirm an eligible reviewer other than the author exists. |
| Bypass | Decide whether protections include administrators and which emergency actors, if any, can bypass. Record their authority and recovery process. |
| Checks | Name the actual required CI jobs after they have run. An enabled status-check option with an empty check list does not select a CI gate. |
| History | Consider linear history and block force pushes/deletions on protected branches. Decide signing and signoff separately; they are different controls. |
| Branch cleanup | Decide automatic topic-branch deletion, automatic PR-head updates, and auto-merge. |
| Security and Actions | Choose dependency/secret scanning, private reporting, allowed actions, fork approvals, and explicit token permissions. |
| Release | Decide whether publishing exists, its triggering events, environments, credentials, reviewers, registry, schedule, and promotion authority. |

### 2. Create the repository and initialize its content

In GitHub, create a repository under the chosen organization and verify its visibility before adding content. Initialize `main` with the agreed license, README, and stack-appropriate ignore rules; avoid generating a second unrelated initial history when importing an existing checkout. Create `development` from the intended initial revision only if that branch model was selected.

Adopt the reviewed engineering-standards snapshot using its bootstrap guide and local Python tooling. Fill in `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, path instructions, and `DEVELOPING.md` for the actual stack and commands. Keep the request manifest and adapters locally owned; synchronization manages only the declared shared snapshot.

Add or customize `.github/CODEOWNERS`, a contribution guide, security policy, PR template, and issue templates. Replace example users/teams, repository links, contact routes, and branch names. Code owners need write access, and team owners need the visibility/access described in [GitHub's CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners). Provide enough eligible ownership coverage to review changes authored by any maintainer. Publish a real private reporting route before directing users to it.

Review **Settings > General** for Issues, Projects, Discussions, Wiki, PR access, and merge options. A public library, internal application, and documentation repository can need different feature settings. Files copied from a template or installed by bootstrap do not establish that server-side protections, environments, secrets, or permissions have been configured; verify each separately.

### 3. Establish CI and Actions permissions

In **Settings > Actions > General**, enable the approved action sources and select read-only default workflow permissions. Leave workflow PR creation/approval disabled unless an identified automation requires it; grant that automation only its needed permissions. Decide the fork-workflow approval policy based on the contribution model. Record whether action SHA pinning or an action allowlist is required.

Add CI for every selected PR target branch. Give validation jobs stable, distinct names and run real build/test commands for the stack. Run a first validation PR so the checks exist before selecting them in protections. Do not treat a command that discovers no tests as evidence of tested behavior.

Keep validation of untrusted PR code separate from publishing. Expose release credentials only to the intended trusted jobs/events. Audit each API call's token requirements: a merged-PR lookup may need `pull-requests: read` in addition to `contents: read`. Add only permissions the workflow uses, following [GitHub's token-permissions guidance](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication).

If a workflow has path filters, do not make its absent check a universal merge requirement. Use an always-triggered required gate that reports a conclusive result when optional work does not apply, or redesign the filtering. [GitHub documents](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpull_requestpull_request_targetbranchesbranches-ignore) that a filtered-out workflow can leave a required check pending.

### 4. Configure branch rules and merge behavior

Choose repository rulesets (**Settings > Rules > Rulesets**) or classic branch protection (**Settings > Branches**) and inspect inherited organization rules first. Record the effective rules, not just the repository-local entries; avoid accidental overlap between mechanisms.

For each selected integration and release branch, configure the agreed PR, review, conversation, history, bypass, and push/deletion settings from step 1. Select actual status-check names and their expected GitHub App source where appropriate, and decide whether branches must be up to date. Verify that the required-check list is populated and that protections cover every intended integration and release branch.

Set squash/merge/rebase availability in **Settings > General > Pull Requests** consistently with the history policy. Configure the default squash message and review the generated title/body before merging under the [Git standard](../standards/git.md). The [GitHub squash settings guide](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests) explains the available title, description, and commit-detail options.

Enable protections after initial content and CI are ready, and verify the chosen maintainer/reviewer model can satisfy them. Do not use an administrator bypass as evidence that ordinary contributor protections work.

### 5. Configure security and release environments

In the repository's security settings, review dependency alerts and security updates, secret scanning and push protection, private vulnerability reporting, and any required code scanning. Select the controls available for the repository's visibility and plan, following the shared security standard. Update the security policy and issue-template contact link to the reporting mechanism actually enabled; do not assume a security policy file enables private reporting.

For repositories that publish or deploy, create only the needed environments in **Settings > Environments**. For example, a two-channel library can use `development` restricted to the `development` branch, and `production` restricted to `main`. Choose required reviewers, self-review prevention, administrator bypass, and secret scope for each environment.

Reference the selected environment on the actual publishing/deployment job. Separate build/PR validation from trusted publish jobs and ensure their conditions prevent publication on PRs or unintended manual runs. Environment protection applies to jobs that reference that environment, as described in [GitHub's environment guide](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments). An unused environment does not gate a publishing step. Do not publish artifacts merely to validate setup without release authorization.

### 6. Read back the configuration

Compare the effective GitHub configuration with the recorded decisions and repository files. With an authenticated GitHub CLI, these PowerShell examples are read-only; replace the repository and branch names:

```powershell
$repository = 'YOUR-ORGANIZATION/YOUR-REPOSITORY'
gh api "repos/$repository"
gh api "repos/$repository/rulesets?includes_parents=true&per_page=100"
gh api "repos/$repository/branches/main/protection"
gh api "repos/$repository/actions/permissions"
gh api "repos/$repository/actions/permissions/workflow"
gh api "repos/$repository/actions/permissions/fork-pr-contributor-approval"
gh api "repos/$repository/environments"
gh api "repos/$repository/private-vulnerability-reporting"
```

For the two-branch model, also inspect `branches/development/protection`. For each environment with custom branch restrictions, inspect `environments/ENVIRONMENT/deployment-branch-policies`. Follow pagination when responses exceed one page. A 404 from the classic protection endpoint can be expected when rulesets supply protection; distinguish it from inaccessible resources using branch metadata and effective rules. A 403 is an unavailable read, not proof of missing protection.

## Required validation

Review effective settings and test an ordinary PR against each intended target branch. Verify eligible owners are requested; an unapproved PR, unresolved discussion, or failing required job blocks merge under the selected policy; passing checks and eligible reviews satisfy it. Include a docs-only PR to catch path-filtered checks that remain pending. Record what was inspected versus exercised; do not merge, deploy, publish, or weaken controls merely to finish this checklist without task authorization.

Check the contribution guide, default PR target, access setting, and branch protection agree. Inspect workflow job permissions, publish conditions, and environment references. Review the generated squash title/body without performing a release. Validate the engineering snapshot, local commands, and links using the repository's established tooling.

## Documentation requirements

Record the setup date, organization/repository, relevant source revisions, selected profile and justified differences, maintainers/code owners, protected branches, named checks, bypass policy, environment bindings, security reporting route, and validation evidence. Exclude credentials, secret values, and sensitive security findings. Mark inaccessible or untested controls explicitly.

## Completion and handoff

Report files prepared, settings actually applied, effective protections and checks, validation outcomes, and decisions still needed. Identify the authorized maintainer for subsequent configuration and release changes. Recommendations and a prepared checklist are distinct from a configured GitHub repository.

## Rollback or recovery

Preserve a reviewed record of previous settings and committed guidance before changing an existing repository. Restore only the affected settings/content under the owner's change process; do not delete a repository, rewrite branch history, expose secrets, or remove protections as an incidental rollback. Recheck the effective rules and CI after recovery.
