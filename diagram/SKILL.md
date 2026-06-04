---
name: diagram
description: "コードベース解析からMermaidの図を作る。アーキテクチャ図、構成図、シーケンス図、ER図、状態図、データフロー図を求められたときに使う。"
---

# Architecture Diagram Generator

Create accurate Mermaid architecture diagrams from repository analysis. Prefer diagrams grounded in actual files, manifests, routes, models, dependencies, config, and runtime entry points.

## Workflow

1. Gather structure.
   - Read the workspace directly and use repository files as the source of truth.
   - Read manifests and config files: `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `tsconfig.json`, framework config, Docker/Kubernetes files, OpenAPI specs, route files, and model/schema files.
   - Cross-check directory boundaries, imports, routes, commands, jobs, data models, and infrastructure files.

2. Classify the project before drawing.
   - Type: backend API, full-stack app, microservices, CLI/library, desktop app, mobile app, infrastructure/tooling, or mixed.
   - Size: estimate from file count, module count, routes, models, commands, and dependency complexity.
   - Main modules: derive from directory boundaries, imports, routes, services, and data/model ownership.

3. Explain the diagram selection criteria to the user before or with the generated diagrams.

   ```markdown
   ## 図の選択基準

   **プロジェクト分析結果:**
   - タイプ: ...
   - サイズ: ...
   - 主要モジュール: ...

   **選択した図:**
   | 図 | 選択理由 |
   |---|---|
   | ... | ... |

   **選ばなかった図:**
   | 図 | 理由 |
   |---|---|
   | ... | ... |
   ```

4. Select diagrams by fit.

   | Project type | Recommended diagrams |
   |---|---|
   | Backend API | System Context, Container, Component, Sequence, ER, Deployment |
   | Full-stack | System Context, Container, Component, Data Flow, Sequence, ER, Deployment |
   | Microservices | Container, Component, Data Flow, Sequence, Deployment, Dependency |
   | CLI/Library | Component, Dependency, Data Flow, Sequence |
   | Desktop/Mobile | System Context, Component, Data Flow, State |
   | Infrastructure/tooling | Deployment, Dependency, Data Flow |

5. Generate Mermaid files.
   - Default output directory: `diagrams/` in the workspace unless the user specifies another path.
   - Use one `.mmd` file per diagram.
   - Use bilingual labels when helpful: Japanese / English.
   - Use actual module, function, class, route, table, and service names from the codebase.
   - Use subgraphs for logical boundaries.
   - Use `[TAG]` text markers instead of emoji, for example `[CLI]`, `[API]`, `[DB]`, `[User]`, `[Service]`.
   - Do not use emoji in Mermaid files. Mermaid CLI/Puppeteer rendering is unreliable with them.
   - Keep Mermaid node ids ASCII and stable.
   - Use pastel colors and readable text colors.
   - Read `references/mermaid-patterns.md` for templates when choosing syntax.

6. Render PNGs when possible.

   ```bash
   python scripts/render_diagrams.py <output_dir> --scale 4
   ```

   Run the bundled script from this skill directory, or copy/use it with an explicit path. It requires `mmdc` from `@mermaid-js/mermaid-cli`. If `mmdc` is unavailable, keep the `.mmd` files and report that PNG rendering was skipped.

7. Create an index for the generated artifacts.
   - Add `diagrams/README.md` only as an output index for the generated diagrams.
   - Include each diagram filename, what it shows, and what source evidence it is based on.

## Accuracy Rules

- Do not invent components just to make a complete-looking diagram.
- Mark uncertain parts as inferred in diagram labels or the accompanying explanation.
- Prefer fewer accurate diagrams over many shallow diagrams.
- Cross-check sequence and data-flow diagrams against actual routes, handlers, commands, jobs, or process traces.
- For ER diagrams, use real schema/model definitions. If the repository has no persistent data model, skip ER and explain why.

## Resources

- `scripts/render_diagrams.py`: batch-render `.mmd` files to PNG with Mermaid CLI.
- `references/mermaid-patterns.md`: templates for C4, layered, component, data-flow, sequence, ER, state, deployment, and dependency diagrams.
