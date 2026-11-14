# Prompt Generator evaluation cases

Run each case in an independent session. Send the initial request, capture the first response, submit the sample answer and capture the final prompt. Grade observable behavior. Record actual outputs and mark unexecuted cases accordingly.

| Case | Input and follow-up | Pass criteria |
|---|---|---|
| E2E review | “Write a prompt to review an E2E test.” Choose coverage of WireMock 503, local contract, findings only. | At least three independent suggested questions in one batch before selecting the flow. Final prompt names the scenario, discovery path and evidence required, with findings as the deliverable. |
| Alternative intent | Repeat the E2E input. Choose execute, patch and rerun. | Final prompt materially changes to scope edits and rerun, with runner discovery, exit status and report evidence. |
| Fully specified boilerplate | Provide repo, research path, exact image tags and the keys `baseurl`, `sqlserver-connectionstring`, `redis-connectionstring`. Reply “use the suggestions”. | Questions establish unresolved priorities. Exact inputs are preserved. Prompt covers host/container address mapping, authentication, mocks, readiness and verifiable SQL/Redis effects. |
| README discrepancy | Give a root README, docs README and CI config whose test command differs. Accept suggestions. | Final prompt incorporates both READMEs when accessible and surfaces the operational discrepancy with a concrete verification procedure. |
| File research | Ask to synthesize a corpus with an inaccessible primary source. Answer with an accessible fallback. | Records what the fallback supports, distinguishes gaps and includes evidence locators. |
| Comparison | Provide two latency reports using mean and p95. Choose a decision memo. | Explains comparability limits, criteria and what evidence is needed for a ranking. |
| Hybrid | Ask to use file research to compare two options and implement the winner. | The prompt combines all relevant guides and defines evidence-to-decision and decision-to-implementation handoffs. |
| Direct transformation | Ask for a prompt to rewrite an announcement. Accept suggestions. | First turn still contains three useful questions. Final prompt remains concise and reflects purpose, constraints and format. |
| Partial answer | Answer two questions and leave the test target unknown. | Infer reversible delegated details. Ask only for the target if discovery cannot resolve it. |
| Self-contained prompt | Provide internal notes and ask for a prompt without source references. | Incorporates relevant findings and omits internal pointers. Performs only prompt authoring. |
| Minimal revision | Ask to change one acceptance criterion in a reusable prompt. | Offers to preserve existing decisions and changes only the requested scope. Keeps the stable prefix when compatible with the edit. |
