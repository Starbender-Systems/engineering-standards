---
name: sb-cpp-engineering
description: Implement and review C++ applications, libraries, and firmware using shared guidance on interfaces, ownership, portability, and validation.
---

# sb-cpp-engineering

## Trigger conditions

Use for C++ features, defects, code review, or language/toolchain maintenance, including C++ firmware.

## Required context

Repository instructions, task acceptance criteria, build/test commands, C++ language mode, compiler and standard library, target platform, and existing style/error-handling configuration. For firmware, also identify the repository's selected embedded guidance and hardware/resource constraints.

## Standards and workflows

[C++](../../standards/cpp.md), [feature development](../../workflows/feature-development.md), [defect investigation](../../workflows/defect-investigation.md), and [code review](../../workflows/code-review.md).

## Procedure

1. Read repository/path instructions and the linked C++ standard; identify the files' actual language and interoperability contracts.
2. Select the applicable workflow and load additional guidance for the affected concerns and target.
3. Inspect ownership, lifetime, ABI, error-handling, and concurrency assumptions before changing the implementation.
4. Implement the scoped change using the existing build system and supported features; validate it on the appropriate targets.

## Validation requirements

Use the repository's build, test, warning/analyzer, and formatting commands. Run relevant lifetime/error-path and portability checks; report sanitizer availability and separate host evidence from target/hardware evidence.

## Safety boundaries

Keep existing exception, RTTI, allocation, compiler, and ABI policies explicit. Use the repository's established hardware/release process when applicable; code changes do not grant authority to flash devices, deploy, publish, or perform destructive operations.

## Completion report

Report changed behavior, toolchain/language/target configuration, commands and results, compatibility or resource effects, and checks or decisions still outstanding.
