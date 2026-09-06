# Experiment specification

Status: proposed pilot, not a frozen publication protocol. Development is authorized by Sai; professor review of the contribution is pending.

## Question and contribution

When a long prompt arrives while other requests are generating tokens, how does SGLang's fixed prefill chunk size change the latency and completed work on an AGX Orin?

The hypothesis is that smaller chunks can reduce interruption of ongoing decoding but increase prefill/scheduling overhead. The result could be positive, negative, or too small to justify a paper. Chunked prefill already exists; the intended contribution is an explained, reproducible tradeoff for the stated Orin configuration.

This is a single-turn, independent-request study. Paused agents, local-tool contention, KV retain/offload/recompute decisions, learned controllers, and adaptive admission remain outside this study and within the broader JouleServe research boundary.

## Pilot contract

Use [the pilot config](../config/pilot.json) for proposed numerical values and [the runtime reference](../config/runtime-reference.json) for inherited image/model identity. Those proposed pilot values have not been validated on a live S1 endpoint.

Null configuration values are intentionally unresolved pilot decisions. Set them during implementation/calibration; the current config is not a runnable campaign specification.

Vary only fixed prefill chunk size. Hold model, precision, attention backend, graph configuration, request cap, total KV-token budget, other launch parameters, and operating state constant. Verify a common feasible token-pool size across all treatments before freezing it.

Start a small group of decodes, then inject a long-prompt request at a recorded offset. Calibrate that offset in the pilot so the arriving prefill actually overlaps active decoding. Reuse the same trace across treatments. Record intended arrival, actual dispatch, and resulting server/client delays; an open-loop arrival schedule must not silently become a completion-paced client.

Tokenize the full chat input, including its template. The longest prompt plus output budget must fit the context limit. Unique leading request tokens should minimize unrelated prefix hits; record actual cached tokens and any shared template prefix. Output limits are caps, not guarantees that generation reaches those lengths.

For these bounded inputs, the largest chunk setting is a **single-chunk control**, not proof that chunking is globally disabled. The existing wrapper accepts positive chunk sizes and rejects the upstream negative disable sentinel. Keep mixed-prefill/decode mode at its installed default and verify actual scheduling behavior; this is not an exact reimplementation of Sarathi-Serve.

## Measurements and correctness

- Timestamp actual request dispatch, first nonempty content, each later content event, completion, usage, errors, and client scheduling delay with monotonic time.
- Report TTFT separately from final response time. SSE content events can contain multiple tokens: their gaps are client-observed delivery gaps, not necessarily inter-token latency. Report aggregate TPOT separately using actual token counts; a true per-token tail needs engine token timestamps.
- Compare arriving-request TTFT, active-request p95 content gaps, successful completed work/second, and prespecified deadline attainment. Record truncation, errors, generated lengths, prefix usage, and any changed task outcomes alongside efficiency.
- Keep functional/diagnostic runs labeled as such. Use independently repeated, randomized paired treatment blocks for claim-bearing data; individual tokens in one run are not independent repetitions.
- Record device, code/config/trace hashes, runtime identity, clocks, temperature, service/co-user state, swap deltas, and allocation observations. Keep failed and invalid windows indexed.

Monitored energy is secondary and requires a valid protocol. The inherited Orin collector defines its primary monitored total as `VDD_GPU_SOC + VDD_CPU_CV + VIN_SYS_5V0`; its separate DDR rail is excluded to avoid double-counting. Verify labels on each board. This is monitored rail energy, not wall-plug energy. Aggregate enough work for the sensor cadence and assess collector overhead; 500 ms samples cannot establish per-token energy. Freeze operating/measurement policy before drawing publication conclusions.

## Pilot exit and limits

The pilot succeeds technically only if all treatments work, input/output accounting is complete, and the trace demonstrates real prefill/decode overlap. It does not succeed scientifically merely because three timings were collected.

Continue toward a paper only if paired evidence reveals a useful explained tradeoff, or a narrowly bounded equivalence result with adequate uncertainty. A noisy null is inconclusive. If the small model exhibits no useful region, report that honestly; a larger model is a separate feasibility decision, not an automatic dependency. Do not create OOM or disruptive memory pressure to manufacture a result.

The first board supports development; the second repeats representative cells. Two AGX Orins provide repeatability within this platform class, not a controlled shared-versus-discrete-memory comparison.

## Origin and references

This specification carries forward S1 from the September 6 ISP proposal packet, originally `HiPC/revised_proposals/01_chunked_prefill.md`, with the user's subsequent decision to start preparation before professor review. This repository is now the working home for S1; the old packet is historical context, not a required sibling checkout.

- [Sarathi-Serve, OSDI 2024](https://www.usenix.org/conference/osdi24/presentation/agrawal): established chunked prefill and scheduling work.
- [Arya and Simmhan, LLM inference on edge accelerators](https://arxiv.org/abs/2506.09554): the lab's offline Orin characterization; S1 instead examines arrival-time interference in streamed serving.
- [SGLang arguments at the inherited commit](https://github.com/sgl-project/sglang/blob/fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1/python/sglang/srt/server_args.py): runtime capability reference; wrapper exposure is a separate constraint.
- [HiPC 2026 SRS call](https://hipc.org/student-research-symposium/): the supplied proposal packet records a September 24 AoE deadline and two pages including references; recheck the call before submission.
