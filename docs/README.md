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

## Recommended Reading Order

If an exact path is supplied, read it directly. Otherwise use this order:

1. **.digest.md** — fast AI orientation (architecture pattern, stack, test commands).
2. **.graph.json** — macro relation graph index for 1-hop document lookup.
3. Selected ADR or feature documents only when their design context is required.

## Construction and QA Planning

Either `blueprint` or `quality-gate plan` can initialize the shared `SCOPE.md`. The former produces `tasks.json` and the latter produces `qa.json`. Use the same scope revision when both plans exist. `forge` executes RED → GREEN and the planned evidence checks. `quality-gate check` judges the candidate-specific evidence when a QA contract applies.


Forge supports implementation, check authoring and execution of existing procedures. Direct mode presents a session plan before writes or side effects. Planned mode maps identified checks to QA obligations and records a start and result per attempt in `tasks.json`. Replanning resets affected execution state while preserving attempt history. Reconcile uncertain external effects by operation key before retrying. Quality Gate records verdicts in `qa.json.assessments`.
