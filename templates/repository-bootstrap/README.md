# Consumer bootstrap

This directory supplies the initial [.agent/manifest.yaml](.agent/manifest.yaml) and [.agent/VERSION](.agent/VERSION). Read the source [README](../../README.md#adopt-a-snapshot) for tool commands and schema details.

## Copy once, then customize

1. Create `.agent/` in the application repository and copy these two bootstrap files without overwriting existing work.
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
