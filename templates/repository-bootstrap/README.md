# Consumer bootstrap

This directory supplies the initial [.agent/manifest.yaml](.agent/manifest.yaml), [.agent/VERSION](.agent/VERSION), and [.agent/.gitattributes](.agent/.gitattributes). Read the source [README](../../README.md#adopt-a-snapshot) for tool commands and schema details.

## One command for every repository type

Configure GitHub hosting with the [repository setup workflow](../../workflows/github-repository-setup.md). Bootstrap installs local guidance only; it does not apply GitHub protections, permissions, environments, or secrets.

Create or clone the target repository first, then run from the engineering-standards root with Python 3.11+ (on Windows, `py -3.12` is an example):

```text
python bootstrap.py ../application-repo
python bootstrap.py ../application-repo --check
```

The default `--type repository` installs this entire common setup: agent adapters, path instructions, prompts, DEVELOPING.md, the request manifest/pin, and the synchronized shared snapshot with its hashes. The bootstrap `.gitattributes` keeps `.agent/` bytes unchanged by Git line-ending conversion, including on Windows.

For a library, the same command also installs the consumer tooling profile:

```text
python bootstrap.py ../example-library --type library --name example-library --display-name "Example Library" --repository https://github.com/example/example-library
```

`--library-ref` defaults to `HEAD` and `--plugin-version` to `0.1.0`. See [the library guide](../../docs/library-consumer-tooling.md) for the additional files and maintenance commands.

All common and type-specific destinations are checked before the first write. Existing identical files retain their modification times; conflicting files, unknown files inside shared snapshot directories, and symlinks/reparse points are rejected and preserved. Exit codes are **0** success/no missing files, **1** missing files under `--check`, and **2** conflict, invalid input, or filesystem error. `--check` never writes. The command does not replace the root README, initialize Git, commit, or install a plugin.

After bootstrapping, fill the local TODOs, select the applicable shared guidance, tune instruction globs, and review the diff. The starter selects all shared content so every initial link resolves. This command initializes a repository; use snapshot synchronization for later shared updates and the library consumer validator for customized tooling.

For existing customized files, use a disposable sibling directory to render the scaffold and merge the relevant differences, or follow the manual steps below. Writes use exclusive creation but the whole run is not transactional; after interruption rerun the same command against the same source checkout and resolve reported conflicts.

## Copy once, then customize

1. Create `.agent/` in the application repository and copy these three bootstrap files without overwriting existing work.
2. Copy or merge [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md), [DEVELOPING.md](../DEVELOPING.md), and the files under [the .github template](../.github/) into matching application paths.
3. Fill local TODOs and select the required shared content in the manifest. The example selects everything, so every starter link resolves.
4. Run synchronization from the matching local standards checkout; it creates the content and hash inventory.
5. Run `--check`, review the complete diff, and commit the snapshot and adapters through a pull request.

Do not copy this bootstrap README over the application's README. Do not replace an existing `.github/` directory wholesale.

## Resulting layout

```text
application-repo/
  AGENTS.md
  CLAUDE.md
  DEVELOPING.md
  .agent/
    .gitattributes
    VERSION
    manifest.yaml
    sync-state.json
    standards/
    workflows/
    skills/
  .github/
    copilot-instructions.md
    instructions/
    prompts/
```

`.agent/` holds a pinned shared snapshot plus a locally owned request manifest. The application owns adapters, architecture, commands, and local constraints. Shared files must not be edited here; propose changes upstream and consume approved updates through reviewable PRs.

Commit the exact pin, manifest, content, and hashes to retain reproducible instruction inputs. Record the source commit in the PR. A pin cannot make model outputs deterministic. Restore the complete prior snapshot to recover previous guidance.

When narrowing selections, transitive shared links are included automatically. Remove unused local adapter templates or update their links to match what the repository uses.

## Optional library profile

The root command's `--type library` performs both the common setup and the library profile. For libraries that already adopted and customized the common baseline, follow the [library consumer tooling guide](../../docs/library-consumer-tooling.md) to use `tools/bootstrap_library.py` for the additions only. Supply the library's own name, repository URL, and Git ref; populate real package versions and capability routes before a release bundle.

This profile does not modify the shared snapshot or replace existing instructions. It rejects conflicting local files before writing; use a disposable sibling directory to render templates for a manual merge when the library already has a marketplace or consumer tooling.
