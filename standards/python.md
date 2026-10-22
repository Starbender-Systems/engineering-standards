# Python engineering

<!-- authority: standard.python -->

## Purpose and scope

Python applications, automation, libraries, and their tests and packaging. These are practical defaults, not a required framework, architecture, package manager, or tool suite. Apply repository-specific instructions, supported runtimes, and existing conventions first; generated code and externally defined interfaces retain their own constraints.

## Rules

### Runtime, environments, and packaging

- MUST use the repository's declared Python versions and isolate environment-specific dependencies. Check language, standard-library, typing, and dependency compatibility against the supported runtime range before introducing newer features; do not silently raise the minimum version.
- SHOULD use the existing environment and installation commands, normally with an isolated virtual environment or equivalent. Keep runtime, build, optional, and development dependencies distinct where supported. Follow the [dependency standard](dependencies.md#rules) for declarations and applicable lock files; libraries and deployed applications can need different version constraints.
- SHOULD use the project's existing packaging metadata and build backend. For new packaged projects, `pyproject.toml` is the standard configuration entry point; declare supported Python versions and required dependencies accurately. Do not migrate package managers, layouts, or build backends incidentally, or add a third-party package when an appropriate supported capability already meets the need.
- MUST preserve public interfaces and document changed runtime or dependency requirements. Include keyword parameter names, import paths, return/error behavior, CLI output and exit codes, and serialized formats when reviewing compatibility.

References: [virtual environments](https://docs.python.org/3/library/venv.html) and [PyPA packaging guidance](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

### Readable style, naming, and documentation

- SHOULD follow [PEP 8](https://peps.python.org/pep-0008/) where the repository has no established convention: four-space indentation, `snake_case` for functions/variables/modules, `CapWords` for classes, and `UPPER_CASE` for constants. Use descriptive names, avoid shadowing built-ins, and follow local import grouping and formatter settings. Line length, quote style, and import sorting remain local choices; avoid unrelated reformatting.
- SHOULD prefer clear control flow and cohesive functions. Use comprehensions for simple transformations, ordinary loops for complex branching or side effects, and `enumerate`, `zip`, and direct iteration when they clarify intent. Distinguish `None` from valid false/empty values with `is None`; use equality for value comparison and identity only when identity is intended.
- SHOULD document public modules and APIs with concise [PEP 257](https://peps.python.org/pep-0257/) docstrings, including non-obvious return, mutation, exception, resource, and iterator-consumption contracts. Explain intent and constraints in comments rather than restating the implementation. Keep the repository's docstring format.
- SHOULD keep imports explicit and avoid wildcard imports and circular dependencies. Separate reusable logic from CLI/framework entry points. Importing a module should not unexpectedly start work, parse process arguments, configure application logging, or perform external I/O; scripts normally use a `main` entry point guarded by `if __name__ == "__main__":`.

### Types, interfaces, and reusable patterns

- SHOULD annotate public interfaces and complex internal contracts using the supported typing syntax and existing type-checking policy. Prefer useful concrete types or collection interfaces to pervasive `Any`; use optional/union types to describe actual outcomes. Type hints and `typing.cast` do not validate values at runtime; validate external data at its boundary. Do not silence diagnostics with broad ignores instead of resolving a contract mismatch.
- SHOULD use ordinary functions and modules for simple responsibilities, and classes when state, invariants, or a meaningful interface justify them. Prefer composition for implementation reuse. Use dataclasses for suitable record-like data and protocols or abstract bases for demonstrated substitutability needs; do not require a class hierarchy, factory, or dependency-injection framework for every operation.
- MUST avoid unintentionally shared mutable defaults in functions and record fields. Use a sentinel such as `None` and create a fresh value per call, or a dataclass `default_factory`. Keep ownership and mutation of caller-provided collections explicit; a shallow copy and a frozen dataclass do not make nested data immutable.
- SHOULD make dependencies and side effects visible at appropriate boundaries so behavior can be tested without global state. Keep return contracts consistent, use keyword-only parameters when they clarify otherwise ambiguous calls, and avoid excessive boolean flags or positional tuples whose meaning is hard to infer.
- SHOULD respect Python's data model when defining equality, ordering, hashing, iteration, and context managers. Keep equality and hashing consistent and avoid changing hash-relevant state while an object is a mapping key or set member. Document whether an iterable is lazy, reusable, or consumed once.

References: [typing](https://docs.python.org/3/library/typing.html), [default argument behavior](https://docs.python.org/3/tutorial/controlflow.html#default-argument-values), [dataclasses](https://docs.python.org/3/library/dataclasses.html), and the [data model](https://docs.python.org/3/reference/datamodel.html).

### Errors, cleanup, and diagnostics

- SHOULD raise meaningful exception types and catch the specific failures that can be recovered from, translated, or reported at that layer. Keep `try` blocks narrow enough to identify the failing operation; preserve causes with `raise ... from exc` when translating and use bare `raise` when rethrowing. Avoid silent broad catches; intentional top-level handling should retain useful diagnostics and a failure outcome.
- MUST use explicit validation for external inputs and necessary side effects rather than relying on `assert`, which can be disabled. Distinguish successful empty/absent results from operational failures. Do not accidentally suppress errors with a return from `finally` or a cleanup handler.
- SHOULD use context managers for files, locks, connections, and other resources with supported lifetime management; use `try/finally` where appropriate. Ensure cleanup on errors and cancellation and define who owns a borrowed resource. Do not rely on garbage collection for timely release.
- SHOULD use the repository's logging conventions for diagnostics, normally a module logger such as `logging.getLogger(__name__)`, with application-level configuration. Reserve CLI stdout for its documented output and keep diagnostic/error channels usable by callers. Include actionable context without secrets, and avoid logging the same exception at every layer.

References: [exceptions and cleanup](https://docs.python.org/3/tutorial/errors.html) and the [logging HOWTO](https://docs.python.org/3/howto/logging.html).

### Data, I/O, and trust boundaries

- MUST use explicit encodings for maintained text files and platform-neutral path handling. Prefer `pathlib` or appropriate `os` path APIs over concatenated separators. Use UTF-8 for new repository text unless an external format requires another encoding; distinguish text from bytes and preserve intentional newline/encoding contracts.
- MUST apply the [security standard](security.md#rules) to untrusted data, file paths, commands, and deserialization. Avoid executing input with `eval`/`exec`, loading untrusted pickle data, or interpolating untrusted values into shell commands or SQL. Use argument lists, parameterized queries, and appropriate safe parsers, while still validating options, paths, shapes, sizes, and permissions for the operation.
- SHOULD use suitable built-in collections and standard-library algorithms before custom machinery. Avoid mutating a collection while iterating unless its contract supports it. Use generators for streaming when useful, while considering deferred errors and resource lifetime; use materialized values when repeated access or ownership requires them.
- SHOULD make units, rounding, time zones, encoding, and ordering assumptions explicit where they affect correctness. Use timezone-aware times for instants, an appropriate monotonic clock for elapsed time, and suitable decimal or integer representations when exact decimal arithmetic is required. Keep filesystem behavior and working-directory assumptions portable.

References: [security considerations](https://docs.python.org/3/library/security_warnings.html) and [aware and naive times](https://docs.python.org/3/library/datetime.html#aware-and-naive-objects).

### Concurrency and performance

- SHOULD choose synchronous code, async I/O, threads, or processes according to the workload and supported deployment runtime. Keep blocking work off an event loop, bound concurrency and timeouts where relevant, and measure before introducing caches, parallelism, or lower-level optimizations. A particular interpreter's GIL behavior is not a general synchronization or performance guarantee.
- MUST define ownership, error propagation, cancellation, and shutdown for background work and shared mutable state. Await or otherwise observe task/future outcomes; avoid unmanaged fire-and-forget work. Use established synchronization primitives rather than assuming compound operations are atomic.
- SHOULD propagate async cancellation after cleanup; swallowing `CancelledError` can break structured concurrency and timeout behavior. Use task groups or other managed task/executor lifetimes when supported and appropriate, and account for process startup, serialization, and platform differences when using multiprocessing.

References: [async tasks and cancellation](https://docs.python.org/3/library/asyncio-task.html) and [executors](https://docs.python.org/3/library/concurrent.futures.html).

## Illustrative example

This standalone Python 3.11+ example keeps parsing separate from file access, uses an explicit encoding and context manager, and returns a new list. The contract preserves order and duplicates, skips blank lines, and propagates file/decoding errors. It illustrates small local files; callers choose size limits and application layout for their use case.

```python
from collections.abc import Iterable
from pathlib import Path


def parse_names(lines: Iterable[str]) -> list[str]:
    """Return stripped nonblank names in input order, preserving duplicates."""
    names = []
    for line in lines:
        name = line.strip()
        if name:
            names.append(name)
    return names


def read_names(path: Path) -> list[str]:
    """Read UTF-8 names; propagate OSError and UnicodeError on failure."""
    with path.open(encoding="utf-8") as source:
        return parse_names(source)
```

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

Improve touched code incrementally and record compatibility constraints when departing from a default.

TODO: Each repository chooses supported Python implementations/versions and platforms, package/environment tooling, dependency and locking policy, formatter/linter/type checker settings, docstring format, test framework, and coverage targets. No new third-party tool or framework is required by this guidance.

## Validation expectations

Run applicable tests and entry points on supported runtimes using repository commands and environments. Apply configured formatting, linting, and type checks without weakening settings to hide new diagnostics. Report unavailable checks separately.

Apply the [testing standard](testing.md#rules) to public behavior, errors, empty and malformed input, encoding/path differences, mutable-state isolation, resource cleanup, and concurrency where affected. Use temporary files and controlled clocks/randomness where practical; isolate external services and mock at meaningful boundaries rather than reproducing implementation details. Import checks and byte compilation alone do not establish runtime correctness.

For packaging changes, build and install the intended artifact into a clean environment and exercise its documented imports/entry points; check supported platform/runtime combinations rather than relying on source-tree imports. Record interpreter/version, commands, outcomes, compatibility effects, and remaining checks.

## Related workflows or skills

- [Feature development](../workflows/feature-development.md)
- [Python engineering skill](../skills/sb-python-engineering/SKILL.md)
- [Defect investigation](../workflows/defect-investigation.md)
- [Code review](../workflows/code-review.md)
- [Dependency update](../workflows/dependency-update.md)
