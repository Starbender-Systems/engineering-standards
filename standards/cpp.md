# C++ engineering

<!-- authority: standard.cpp -->

## Purpose and scope

C++ applications, libraries, and firmware, including their public interfaces and build configuration. These are practical defaults rather than a prescribed architecture, naming scheme, build system, or language-version upgrade. Apply repository-specific instructions and existing conventions first. C-compatible headers and externally defined interfaces retain their language and interoperability requirements.

## Rules

### Toolchain, portability, and readable style

- MUST use the repository's declared C++ language version, compilers, standard library, target architecture, and build configuration. Preserve its exception, RTTI, ABI, and runtime-library settings unless changing them is part of the task. Check feature availability before adopting newer syntax or library facilities; compiler support alone does not establish library support.
- SHOULD follow existing naming, indentation, brace placement, file layout, and `.clang-format` or equivalent configuration. Use descriptive names, cohesive functions, clear control flow, and comments explaining non-obvious invariants or constraints. Avoid unrelated formatting rewrites or arbitrary function-length limits.
- SHOULD use `auto` when it makes types easier to understand or avoids repetition, and explicit types when they clarify interfaces or conversions. Check whether deduction copies a value or preserves a reference/const qualification. Prefer named constants and small functions over macros when equivalent; retain macros where preprocessing is necessary.
- MUST keep platform/compiler extensions and C interoperability intentional and contained at established boundaries. Preserve linkage, calling conventions, layout/alignment, and allocation/deallocation contracts across binary or foreign-language interfaces. Follow [architecture](architecture.md#rules) and [dependency](dependencies.md#rules) guidance when changing those boundaries or introducing libraries.

References: [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) and [Microsoft's modern C++ overview](https://learn.microsoft.com/en-us/cpp/cpp/welcome-back-to-cpp-modern-cpp).

### Ownership, resources, and lifetimes

- SHOULD tie resource cleanup to an owning object's lifetime using RAII: acquire a file, allocation, lock, or handle into a suitable owner and release it on scope exit, including failure paths. Prefer standard containers and existing resource wrappers over scattered manual cleanup. Wrap unavoidable C/platform handles with their correct release operation.
- SHOULD prefer values and automatic storage where suitable. Use `std::unique_ptr` for exclusive dynamic ownership and `std::shared_ptr` only when ownership is genuinely shared; reference counting is not a reason to share every object. Review ownership cycles and use a non-owning relationship such as `std::weak_ptr` where appropriate. Prefer factory helpers such as `std::make_unique` when supported and applicable.
- MUST make owning versus borrowing contracts clear. Raw pointers and references normally express borrowing; legacy/C ownership-transfer contracts need explicit documentation or a wrapper. A pointer passed to an observing function does not transfer ownership by itself. Use a required reference or nullable pointer according to the API's semantics, rather than assuming every pointer may be null.
- MUST keep borrowed objects alive for their entire use. This includes references, iterators, lambda captures, `std::string_view`, and `std::span` where available. Check invalidation after mutation/reallocation and asynchronous escape; a view's bounds or const access do not extend the owner's lifetime. Return an owning value when a borrowed result cannot safely outlive its source.

See [smart pointer guidance](https://learn.microsoft.com/en-us/cpp/cpp/smart-pointers-modern-cpp), [object lifetime rules](https://eel.is/c++draft/basic.life), and [string-view semantics](https://learn.microsoft.com/en-us/cpp/standard-library/basic-string-view-class).

### Types, interfaces, and reusable patterns

- SHOULD establish valid object state during initialization and keep invariants behind a small API. Initialize scalar members deliberately; use constructor member initializers or default member initializers rather than assignment after construction. Prefer `const` access when mutation is not intended, while recognizing that constness alone does not guarantee thread safety.
- SHOULD use the rule of zero: let members with well-defined ownership implement destruction, copying, and moving. If custom resource management requires special members, decide copy/move/destruction semantics together; explicitly default or delete operations as appropriate. Do not use `std::move` merely to make code look efficient: it permits moving but does not itself transfer a resource.
- SHOULD use values and composition for ordinary implementation reuse. Use inheritance for an intentional substitutable interface, and mark overrides with `override`. Provide safe polymorphic destruction when deleting through a base interface, or prevent such deletion by design; avoid object slicing when passing polymorphic objects by value.
- SHOULD keep inputs and outputs explicit. Pass small values cheaply by value, use const references or views for appropriate borrowing, and return result values instead of unnecessary output parameters. Use `explicit` constructors/conversions when implicit conversion would surprise callers, and named/scoped enums when they improve type safety.
- SHOULD choose templates, dynamic dispatch, factories, or type erasure for a demonstrated need. Document generic requirements and use constraints/concepts only where supported and useful. Keep metaprogramming understandable; do not impose a pattern framework or an interface for every concrete type. Consider ABI and compile-time costs before exposing implementation details or introducing PImpl/header-only designs.

References: [construction and initialization](https://learn.microsoft.com/en-us/cpp/cpp/constructors-cpp), [const correctness](https://isocpp.org/wiki/faq/const-correctness), and [virtual-function/destructor guidance](https://isocpp.org/wiki/faq/virtual-functions).

### Headers and source organization

- SHOULD make headers self-contained: include the declarations they use, avoid relying on incidental transitive includes, and use the project's include guards or supported equivalent. Include the corresponding header early in its implementation file so missing dependencies are detected. Keep public headers small and stable where practical.
- MUST respect the one-definition rule and linkage when placing definitions in headers, templates, modules, and source files. Use `inline` or other appropriate language mechanisms for shared definitions; it is not a promise of optimization. Preserve the project's header/module strategy rather than converting it incidentally.
- SHOULD avoid namespace-wide `using` directives in public headers and keep implementation names out of public namespaces. Avoid identifiers reserved to the implementation, such as names containing double underscores. Limit macro scope and document required feature/configuration macros; do not introduce global macro pollution to shorten ordinary code.

See [header organization guidance](https://learn.microsoft.com/en-us/cpp/cpp/header-files-cpp).

### Errors, exceptions, and contracts

- MUST follow the repository's error-handling model. Distinguish successful empty/absent results from invalid input and operational failure. Use the established exception, status, or result contract consistently and handle significant failure results; consider `[[nodiscard]]` where supported and ignoring a result would be erroneous.
- SHOULD use assertions for internal assumptions, not as the only validation of external input or as a place for necessary side effects; assertions can be disabled. Apply the [security standard](security.md#rules) at input and trust boundaries.
- When exceptions are enabled, SHOULD throw meaningful typed failures and catch by const reference where appropriate. Catch where recovery, translation, or necessary boundary handling occurs; use `throw;` to rethrow the same exception without slicing. Maintain documented invariants and resource safety if an operation fails, and specify a stronger rollback guarantee where callers need it.
- MUST keep destructors and cleanup from propagating exceptions. Declare `noexcept` only when its guarantee is valid; an escaping exception otherwise terminates the program. Do not allow exceptions to escape a C ABI, callback, or other boundary that cannot transport them. In exception-free code, provide explicit failure paths rather than silently treating failed acquisition or initialization as success.

References: [exception design guidance](https://isocpp.org/wiki/faq/exceptions) and [compiler exception-handling configuration](https://learn.microsoft.com/en-us/cpp/cpp/exception-handling-in-visual-cpp).

### Containers, conversions, and data correctness

- SHOULD prefer standard containers, strings, and algorithms when they fit the target. Choose a loop when it expresses the operation more clearly. Pass lengths with buffers, respect iterator/range validity, and check bounds according to the contract. A string view is not necessarily null-terminated; preserve encoding and termination requirements at interfaces.
- MUST avoid undefined behavior, including invalid lifetime use, out-of-bounds access, uninitialized reads, invalid aliasing/alignment, signed overflow, and unsafe concurrent access. Validate sizes, arithmetic, and signed/unsigned conversions before they can corrupt bounds or allocations. Review narrowing conversions and choose numeric types for the domain rather than using casts to silence warnings.
- SHOULD prefer named C++ casts when conversion is needed so intent is visible. Keep reinterpretation, const removal, raw byte manipulation, and platform-level access narrow and justified. Use the target's supported representation/serialization facilities rather than assuming an in-memory layout is a portable wire format.
- SHOULD preserve normal value semantics for reusable value types, including consistent comparison and hashing where implemented. Avoid mutating key properties while a value is stored in an associative container. Document units, precision/rounding, and time/encoding assumptions when those affect correctness.

See [modern standard-library usage](https://learn.microsoft.com/en-us/cpp/cpp/welcome-back-to-cpp-modern-cpp) and [undefined-behavior checks](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html).

### Concurrency and performance

- MUST synchronize access to shared mutable state and define thread/task ownership and shutdown. `volatile` is not a thread synchronization mechanism, and a thread-safe smart-pointer control block does not make its pointed-to object thread-safe. Review captures and borrowed state before work outlives its initiating scope.
- SHOULD use scoped locking and existing synchronization primitives instead of manual lock/unlock or custom lock-free algorithms. Define a consistent lock order, keep critical sections small, and avoid calling unknown callbacks while holding a lock unless the design accounts for reentrancy and blocking. Use explicit thread join/shutdown or an appropriate joining owner such as `std::jthread` when supported.
- SHOULD start with understandable algorithms and suitable data structures, then optimize using representative measurements. Consider complexity, I/O, allocation, and contention before pooling, custom allocators, SIMD, or low-level tricks. Avoid gratuitous copies, but preserve valid lifetime/ownership contracts when replacing them with views or moves.
- For constrained targets, MUST honor documented stack/heap, interrupt, timing, and runtime restrictions. Check whether library operations allocate, block, or throw in the relevant execution context. A host test or sanitizer result does not establish target timing or hardware safety.

See [C++ concurrency guidance](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-concurrency) and [ThreadSanitizer's supported checks/platforms](https://clang.llvm.org/docs/ThreadSanitizer.html).

## Illustrative example

This standalone C++17 example uses an owning stream for RAII and returns an owning string, distinguishing an empty file from I/O failure. It illustrates an exception-enabled application contract; exception-free/firmware projects use their chosen result mechanism instead. The function naming and brace style are illustrative, not a required migration or language-version selection. An explicit close/check would be needed if successful resource finalization were part of an output contract.

```cpp
#include <fstream>
#include <optional>
#include <stdexcept>
#include <string>

namespace example
{
std::optional<std::string> read_first_line(const std::string& path)
{
    std::ifstream input{path};
    if (!input)
    {
        throw std::runtime_error{"Unable to open input file."};
    }

    std::string line;
    if (std::getline(input, line))
    {
        return line;
    }

    if (input.eof() && !input.bad())
    {
        return std::nullopt;
    }

    throw std::runtime_error{"Unable to read input file."};
}
}
```

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation). Record relevant target, ABI, interoperability, or measured performance constraints when departing from a default. Improve touched code incrementally rather than applying a broad modernization as unrelated work.

TODO: Each repository chooses its language baseline, supported toolchains/platforms, build/package system, naming/formatting, analyzer/formatter configuration, exception and RTTI policy, allocation limits, and ABI commitments. No dependency on a guideline library, testing framework, or particular build system is established here.

## Validation expectations

Build with the declared compiler, language mode, target, and agreed warning/analyzer settings; review new diagnostics without weakening the baseline to hide them. Run affected tests and formatting checks using repository commands. Check standalone headers or multiple translation units when relevant to include/linkage changes, and use the supported compiler/platform matrix for portability claims.

Apply the [testing standard](testing.md#rules) to ownership/lifetime, empty and malformed input, boundary sizes and conversions, copy/move behavior, error paths, and concurrency when affected. Use available host tools such as [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html), [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html), or a separate supported ThreadSanitizer configuration when appropriate. Sanitizers test exercised paths and have platform/runtime limits; record unavailable checks and do not treat them as proof that undefined behavior is absent.

For firmware, also follow the repository's selected embedded guidance and record the actual hardware/toolchain evidence. Report the commands, compiler/standard-library versions, target configuration, observed results, and remaining runtime or hardware checks.

## Related workflows or skills

- [C++ engineering skill](../skills/sb-cpp-engineering/SKILL.md)
- [Feature development](../workflows/feature-development.md)
- [Defect investigation](../workflows/defect-investigation.md)
- [Code review](../workflows/code-review.md)
