# Project Documentation

Index of project technical documentation for **Agentic Workbench**. Coding agents start here when `docs/` exists; follow the links for architecture, conventions and testing before making changes.

## Documentation Index

| Document | Description | Reading |
|----------|-------------|----------|
| [**.digest.md**](./.digest.md) | Fast-path machine-readable orientation digest (stack, test commands, rules). | **Mandatory** |
| [**.graph.json**](./.graph.json) | Macro relation graph index for agent topology navigation and 1-hop routing. | **Mandatory** |
| [**ARCHITECTURE.md**](./adr/ARCHITECTURE.md) | Architecture, folder organization, and code patterns for the project. | **Mandatory** |
| [**TESTS.md**](./adr/TESTS.md) | Testing strategies, patterns, and execution commands. | **Mandatory** |
| [**PROJECT-MAPPER-RESEARCH.md**](./adr/guides/PROJECT-MAPPER-RESEARCH.md) | Reverse-engineering research and falsification plan for the proposed standalone Project Mapper skill. | Optional |
| [**PROJECT-MAPPER-REA.md**](./adr/guides/PROJECT-MAPPER-REA.md) | REA source, evidence, traversal and version comparison deep dive. | Optional |
| [**PROJECT-MAPPER-METHOD.md**](./adr/guides/PROJECT-MAPPER-METHOD.md) | Comparative research and architecture recovery method. | Optional |
| [**PROJECT-MAPPER-VALIDATION.md**](./adr/guides/PROJECT-MAPPER-VALIDATION.md) | Local graph contract, refresh and experimental acceptance criteria. | Optional |

## Recommended Reading Order

If an exact path is supplied, read it directly. Otherwise use this order:

1. **.digest.md** — fast AI orientation (architecture pattern, stack, test commands).
2. **.graph.json** — macro relation graph index for 1-hop document lookup.
3. Selected ADR or feature documents only when their design context is required.

## Construction and QA Planning

`blueprint` records the specification in `context.sqlite` and renders `SCOPE.md`. Its optional Forge export becomes a revision-bound `tasks.json` when Forge publishes it. `quality-gate plan` produces `qa.json`; if no Blueprint database exists it can initialize a standalone scope. Reconcile the scope and QA revisions before execution. `forge` executes RED → GREEN and planned evidence checks. `quality-gate check` judges candidate-specific evidence.


Forge supports implementation, check authoring and execution of existing procedures. Direct mode presents a session plan before writes or side effects. Planned mode maps identified checks to QA obligations and records a start and result per attempt in `tasks.json`. Replanning resets affected execution state while preserving attempt history. Reconcile uncertain external effects by operation key before retrying. Quality Gate records verdicts in `qa.json.assessments`.

`blueprint` and `forge` can query an existing `.project-mapper/graph.sqlite` in the mapper's Git-free read-only mode. They verify consequential current sources and treat partial or stale map results as leads.
