---
name: flow-visualizer
description: "システムやコードパスの流れをASCIIフロー図で説明する。仕組み、全体像、処理フロー、実行経路を知りたい依頼で使う。"
---

# Flow Visualizer

Explain a system with a detailed vertical ASCII flow: processing steps, code-level anchors, commands, files, functions, exit codes, and short natural-language explanations.

## Output Style

Use this structure as the default:

```text
  Input or trigger
        |
        v
  +--------------------------------------------------------------+
  | Step 1: Process name                                         |
  | What happens, with file/function/command details.             |
  +--------------------------------------------------------------+
        |
        v
  +--------------------------------------------------------------+
  | Step 2: Process name                                         |
  | +----------------------------------------------------------+ |
  | | Sub-flow                                                  | |
  | | - Important internal operation                            | |
  | | - Programming-layer anchor                                | |
  | +----------------------------------------------------------+ |
  +--------------------------------------------------------------+
        |
        v
  Final output or observable result
```

Use ASCII characters for boxes and arrows unless the user explicitly wants Unicode box drawing.

## Explanation Rules

- Include programming-layer anchors: file paths, functions, classes, commands, exit codes, environment variables, routes, database tables, queues, jobs, and config files.
- Keep the abstraction at the processing-unit level. Do not explain every line of code unless the user asks.
- Explain what each step accomplishes and why it exists.
- Use nested boxes for sub-flows when a step contains meaningful internal work.
- Keep each step compact: usually 1-3 lines inside a box.
- If the user asks about a repository, inspect the relevant files before drawing the flow.
- If part of the flow is inferred rather than verified, label it as inferred.

## Repository Workflow

1. Identify the entry point: command, route, handler, UI action, job, test runner, or public API.
2. Trace the next calls using `rg`, manifests, imports, route definitions, and config files.
3. Capture the main path first, then add important branches such as validation failure, retries, or error handling.
4. Produce the ASCII flow.
5. Add a short note after the diagram only when it clarifies assumptions, skipped branches, or source files.

## Example

```text
$ go test ./...
      |
      v
+--------------------------------------------------------------+
| 1. Discover packages and test files                           |
| `go` walks packages and finds `*_test.go` files.              |
+--------------------------------------------------------------+
      |
      v
+--------------------------------------------------------------+
| 2. Compile a temporary test binary                            |
| Test functions, package code, and generated test main compile.|
+--------------------------------------------------------------+
      |
      v
+--------------------------------------------------------------+
| 3. Execute tests and collect status                            |
| PASS exits 0. Failing tests return non-zero with diagnostics.  |
+--------------------------------------------------------------+
      |
      v
Result printed to stdout/stderr
```
