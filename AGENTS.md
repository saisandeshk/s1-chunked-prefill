# S1 working instructions

Read `PLAN.md` when continuing work. Read `docs/EXPERIMENT.md` before changing the workload, treatment matrix, metrics, or research scope. Read `docs/DEVELOPMENT.md` before implementing device integration or coordinating checkouts.

- Sai has authorized S1 preparation and prototyping while professor review is pending. Record that review separately from technical progress; do not invent professor approval or repeatedly request permission for already-authorized work.
- Keep this a fixed-chunk, independent-request characterization study. JouleServe retains the paused-session KV, tool-contention, and adaptive admission/controller questions.
- Use `config/pilot.json` for proposed treatment values and `config/runtime-reference.json` for inherited artifact identity. A reference to an old successful run does not validate a new S1 configuration.
- Make client/analysis code usable on Python 3.10+ without importing the GPU serving stack. Resolve project files relative to the checkout or explicit CLI arguments; keep device-specific paths in ignored local configuration.
- Before using an Orin's JouleServe checkout, read its operating instructions. Route Docker work through the existing restricted wrapper. Preserve the approved image/model and the device's other workloads; do not broaden privileges or alter clocks as a side effect.
- Record request timing from streamed content, distinguish SSE delivery gaps from token-level gaps, and preserve failed runs. Publication claims require a frozen measurement protocol and evidence.
- Keep raw run directories local. Curated results must identify code/config/input hashes and the device. Prefer clean, committed code for campaigns and record any diagnostic dirty patch explicitly.
- Verify changes at their scope, then update `PLAN.md` with evidence and the next concrete step. Do not add placeholder success results or tests that merely assert implementation structure.
