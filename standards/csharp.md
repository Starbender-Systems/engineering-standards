# C# conventions

<!-- authority: standard.csharp -->

## Purpose and scope

C# source, public APIs, and code review. These conventions provide a practical baseline; they do not select an application architecture, framework, or analyzer package. Apply the repository's documented instruction precedence and local constraints; platform instructions and permissions remain in force.

## Rules

### Consistency and readable style

- MUST follow the repository's `.editorconfig`, formatter, analyzer configuration, and supported language version. Apply the [.NET standard](dotnet.md#rules) for SDK/framework and existing nullable/analyzer settings. Treat generated code and externally defined contracts according to their own tooling and compatibility constraints.
- SHOULD use descriptive names and straightforward control flow. Prefer cohesive methods, guard clauses for invalid inputs, and expressions that a reader can understand without unpacking several side effects. Extract helpers around meaningful responsibilities rather than enforcing arbitrary line or method-length limits.
- SHOULD use consistent indentation, whitespace, braces, and member layout. In new code without an established style, four-space indentation, braces on separate lines, and braces around control-flow bodies are reasonable defaults. Avoid unrelated reformatting.
- SHOULD use `var` when the type is clear from the expression and an explicit type when it clarifies meaning, conversions, or a public contract. Use built-in type keywords such as `string` and `int` consistently with local style. Choose expression-bodied members, pattern matching, and newer syntax for clarity rather than novelty.

These defaults draw on [Microsoft's common C# conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions), which are examples of conventions rather than universal requirements.

### Naming and source organization

- SHOULD use `PascalCase` for namespaces, types, methods, properties, events, and constants, and `camelCase` for parameters and local variables. Prefix interface names with `I`, and use meaningful generic parameter names such as `T` or `TResult`. Follow the repository's private-field naming convention; `_camelCase` is a common default, not a required migration.
- SHOULD use names that communicate domain meaning and behavior: verbs for actions, nouns for types/properties, and readable predicates such as `IsReady` or `HasAccess`. Prefer recognized terms over unexplained abbreviations, type-encoding prefixes, or vague names such as `Helper` and `Manager` without a clear responsibility.
- SHOULD suffix awaitable operations with `Async` where their framework/interface contract permits, and name a cancellation parameter `cancellationToken`, normally last. Preserve established API and serialized names when changing naming would break consumers.
- SHOULD organize namespaces and files by their established feature or responsibility. Keep primary type and file names aligned where practical; related small types can share a file when that improves navigation. Generated types, partial types, and framework conventions can justify different layouts.

See [Microsoft's identifier naming guidance](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/identifier-names).

### Types, contracts, and nullability

- SHOULD expose the smallest useful API surface and keep implementation details private or internal. Prefer properties to public mutable fields, and constructor initialization or `readonly` state when values should not change. Use methods for operations with significant work or side effects.
- SHOULD express optional values with nullable annotations when enabled and establish valid object state at construction/boundaries. Nullable analysis does not replace runtime checks for caller or external input. Prefer making invariants clear over scattering null-forgiving operators, `default!`, or broad warning suppressions; document a narrow suppression's rationale when the invariant is not evident.
- SHOULD distinguish absence, an empty result, invalid input, and operational failure in the API contract. Return empty collections when that means a successful result with no items; do not use empty/default values to conceal failures. Validate arguments before externally visible effects and use `nameof` for parameter names in diagnostics.
- SHOULD choose classes, records, structs, and enums for their semantics. Records suit data with value-based equality; they do not guarantee deep immutability of referenced objects. Use small immutable structs for genuine value semantics, and named enum values for a defined set of choices. Avoid converting identity-based entities to records solely for shorter syntax.
- MUST keep equality and hashing consistent when implementing them; avoid mutating equality/hash inputs while an object is used as a dictionary key or set element. Preserve API, serialization, and persistence compatibility when changing a type's representation.

References: [nullable reference types](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/null-safety/nullable-reference-types), [type design](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/type), [record semantics](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/record), and [equality/hash contracts](https://learn.microsoft.com/en-us/dotnet/api/system.object.gethashcode).

### Responsibilities and dependency boundaries

- SHOULD keep types focused and prefer composition/delegation when inheritance does not model a real substitutable relationship. Introduce interfaces at useful boundaries, such as external services or interchangeable behavior; an interface for every class is not a goal.
- SHOULD make dependencies explicit, normally through constructor injection when the application uses DI. Keep service resolution in the established composition/factory boundary rather than hiding dependencies behind a global service locator. Create ordinary value objects directly when no service boundary is needed.
- MUST respect dependency scopes and ownership: do not retain a scoped service in a singleton or dispose a container-owned dependency. Use an explicit scope/factory where a longer-lived operation needs shorter-lived services. Apply the [.NET resource-lifetime rules](dotnet.md#rules) to resources the code owns.
- SHOULD keep reusable logic independent of ambient clocks, configuration, transport, or mutable global state where those dependencies affect behavior or tests. Use the project's existing boundary or a small abstraction when needed; do not introduce a framework solely to apply a pattern.

Follow [architecture guidance](architecture.md#rules) for changes to established boundaries and [dependency guidance](dependencies.md#rules) for new packages. Repository, unit-of-work, mediator, CQRS, and similar patterns are choices to justify, not a mandatory stack. See [Microsoft's DI guidance](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines).

### Asynchronous code and concurrency

- SHOULD return `Task` or `Task<T>` for ordinary asynchronous APIs; reserve `async void` for signatures such as event handlers that require it. Use `ValueTask` or asynchronous streams when the contract or measured behavior warrants their added constraints.
- MUST observe completion and failures of started tasks. Detached/background work needs an explicit owner for error reporting, lifetime, and shutdown; assigning a task to `_` does not establish that ownership.
- SHOULD use asynchronous I/O directly instead of wrapping it in `Task.Run`. Bound parallel work to the resource and workload, and avoid sharing mutable state or non-thread-safe services across concurrent operations. Review failure and cancellation behavior when coordinating multiple tasks.
- Apply the [.NET cancellation and nonblocking rules](dotnet.md#rules). Choose `ConfigureAwait` behavior according to library/host context and existing policy; do not impose one choice on all UI, server, and library code.

See [Microsoft's async guidance](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/) and [common async bugs](https://learn.microsoft.com/en-us/dotnet/standard/asynchronous-programming-patterns/common-async-bugs).

### Exceptions and diagnostics

- SHOULD use the existing contract for expected outcomes, such as `TryParse`, a nullable lookup, or an established result type. Use appropriate standard exceptions for invalid arguments, invalid state, and failures; introduce custom exception types only when callers need their additional meaning.
- MUST catch exceptions only where the code can recover, translate at an appropriate boundary, or perform necessary handling before propagation. Do not silently discard failures or report cancellation as success. Preserve the original stack with `throw;` when rethrowing the same exception; preserve the cause when translating it.
- SHOULD log actionable context at the boundary responsible for handling a failure, avoiding repeated logs at every layer. When structured logging is available, use stable message templates and named properties rather than interpolated messages, and pass exceptions through the logger's exception argument. Apply the [security standard](security.md#rules) to diagnostic data.

See [exception best practices](https://learn.microsoft.com/en-us/dotnet/standard/exceptions/best-practices-for-exceptions) and [.NET structured logging](https://learn.microsoft.com/en-us/dotnet/core/extensions/logging/overview).

### Collections, LINQ, and performance

- SHOULD select collection contracts by caller needs: enumeration, count/index access, or mutation. Use generic collections and avoid exposing mutable internal collections accidentally. An `IReadOnlyList<T>` view alone does not make the underlying data immutable.
- SHOULD keep LINQ transformations understandable and free of surprising side effects; use a loop when it better expresses control flow. Account for deferred execution, repeated enumeration, and the lifetime of the underlying source. Materialize deliberately when a stable snapshot or single evaluation is required, rather than adding `ToList` everywhere.
- SHOULD preserve query-provider boundaries: filtering an `IQueryable<T>` and filtering an in-memory `IEnumerable<T>` can have different execution/cost. Review data transfer and generated-query behavior when persistence queries change, following the repository's existing persistence approach.
- SHOULD optimize using representative measurements. Consider algorithmic complexity and I/O before allocation tricks, pooling, spans, or unsafe code; retain correctness and clear ownership when an optimization is justified.

See [LINQ execution guidance](https://learn.microsoft.com/en-us/dotnet/csharp/linq/get-started/introduction-to-linq-queries).

### Strings, values, and documentation

- SHOULD make comparison intent explicit: use ordinal comparison for nonlinguistic identifiers and culture-aware behavior for human-language text where needed. Specify the appropriate `StringComparison` or `StringComparer`; case sensitivity follows the domain contract, not a universal default. Use invariant formats for machine interchange when the protocol requires them.
- SHOULD select numeric and time types by domain semantics. `decimal` is generally suitable for base-10 financial values, with explicit currency and rounding rules. Represent instants unambiguously, for example with `DateTimeOffset` or a documented UTC convention; distinguish instants, local schedules, dates, and durations. An offset is not a time-zone identifier.
- SHOULD explain non-obvious intent, invariants, ownership, and compatibility in comments or API documentation. Document public contract details such as null results, exceptions, side effects, and cancellation when they are not clear from the signature. Avoid comments that only repeat the code.

See [string comparison guidance](https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-strings), [numeric type guidance](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/floating-point-numeric-types), and [date/time type guidance](https://learn.microsoft.com/en-us/dotnet/standard/datetime/choosing-between-datetime).

## Illustrative example

This example shows naming, an explicit dependency, argument validation, nullable lookup results, and cancellation forwarding. Types are grouped to make it standalone; project file layout, field prefixes, and use of `sealed` or records remain local choices. It uses C# 10 syntax with nullable annotations enabled and does not select a repository's language version.

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;

namespace Example.Orders;

public sealed record Order(string Id);

public interface IOrderStore
{
    Task<Order?> FindAsync(string orderId, CancellationToken cancellationToken);
}

public sealed class OrderLookup
{
    private readonly IOrderStore _orders;

    public OrderLookup(IOrderStore orders)
    {
        _orders = orders ?? throw new ArgumentNullException(nameof(orders));
    }

    public Task<Order?> FindAsync(
        string orderId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(orderId))
        {
            throw new ArgumentException("An order identifier is required.", nameof(orderId));
        }

        return _orders.FindAsync(orderId, cancellationToken);
    }
}
```

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation). Prefer consistency within an established codebase over a broad style migration; record relevant contract, tooling, or performance reasons for deviations.

TODO: Each repository chooses its formatting details, private/static field prefixes, namespace form, `var` preferences, analyzer packages/severities, documentation coverage, and language-feature adoption. This standard does not mandate an analyzer dependency, a design-pattern library, or a particular architecture.

## Validation expectations

Use the declared SDK and the repository's existing build, analyzer, formatting, and affected-test commands. If `dotnet format --verify-no-changes` is part of that toolchain, use the agreed project/solution and scope; do not run a broad formatting rewrite incidentally. Review new warnings rather than weakening settings to hide them.

Apply the [testing standard](testing.md#rules) to changed contracts, including null/empty inputs, expected failures, cancellation, disposal, equality, culture, and concurrency where relevant. Check serialized/public APIs and query behavior when affected. Report commands, results, and checks that could not run.

## Related workflows or skills

- [.NET engineering](dotnet.md)
- [.NET engineering skill](../skills/sb-dotnet-engineering/SKILL.md)
- [Feature development](../workflows/feature-development.md)
- [Code review](../workflows/code-review.md)
