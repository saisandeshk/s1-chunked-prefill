# Submission and related-work evidence

Accessed 2026-09-07. This note verifies public requirements and source semantics; it does not establish live runtime behavior or experimental results. Recheck the call and submission form immediately before submission. The user has authorized experiments and drafting now; administrative submission requirements remain separate.

## HiPC 2026 SRS

The [official SRS call](https://hipc.org/student-research-symposium/) specifies:

| Item | Requirement |
|---|---|
| Deadline | September 24, 2026, AoE; notification November 1; camera-ready November 23 |
| Manuscript | PDF; at most two pages including references; single-spaced, double-column, 10-point, US Letter, one-inch margins; IEEE conference style |
| Submission | [Linklings](https://ssl.linklings.net/conferences/HiPC/) |
| Eligibility | At least one author is a student during 2026; mark student authors with `*` and state their degree; identify lead author's undergraduate/postgraduate/PhD category |
| Advisor | Signed undertaking attesting originality and student execution |
| Exclusivity | No concurrent consideration at another conference track, including HiPC, or journal |
| Anonymity | No explicit anonymous-review requirement on this call; author-identification instructions are present |
| Scope | HPC, AI, accelerators, edge, quantum |
| Publication | Accepted two-page abstracts enter HiPC Workshop proceedings/IEEE Xplore; a student must register and present |
| Suggested structure | Introduction, design, evaluation, conclusion/future work, references |
| AI text | Acknowledgment and citations to the generating system in affected sections |

The call does not identify final poster dimensions. Lead-author degree, final author list, affiliations, and advisor signature require authentic author-supplied information, not inferred credentials. The undertaking is a submission artifact, not a prerequisite to the authorized experiments.

**Formatting issue:** the call's explicit one-inch margins differ from the dimensions in an [IEEE-hosted conference-template example](https://ewh.ieee.org/soc/ras/conf/technicallycosponsored/icar/icar2017/www.ee.cuhk.edu.hk/_qhmeng/icar2017/assets/ieee_conference_paper_template.pdf), which uses narrower side margins. This example is historical, not a 2026 rule. Start from the [IEEE Author Center's conference template resources](https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/), retain the stricter call geometry for the draft, and inspect the final PDF. Do not silently assume an unmodified `IEEEtran` layout satisfies the call. Reconcile any submission-form/template discrepancy before uploading.

The [IEEE AI-content policy](https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/) additionally covers generated figures, images, and code appearing in articles. Disclosure identifies the system, affected sections, and extent of assistance. For this project, maintain accurate records of assistance and distinguish measurements collected on hardware from generated prose. An acknowledgment cannot substitute for a student's review, understanding, and authentic advisor undertaking.

## Prior work and the contribution boundary

**Sarathi-Serve.** Agrawal et al. split prefills into chunks and combine this with stall-free scheduling to improve the throughput/latency tradeoff. Their reported platforms include A100 deployments and pipeline-parallel serving; the published work already establishes the scheduling idea. S1 must not claim to invent chunked prefill, to reproduce their scheduler merely by changing an SGLang flag, or to inherit their reported performance gains. [USENIX paper and bibliographic record](https://www.usenix.org/conference/osdi24/presentation/agrawal).

**Arya and Simmhan.** Their Orin AGX 64GB study uses PyTorch 2.3.0 and Hugging Face Transformers, JetPack 6.0/CUDA 12.2, WikiText2/LongBench, and four models spanning 2.7B–32.8B. It varies batch size, combined input/output length, quantization, and power modes. Its metrics include batch completion latency and throughput counting input plus output tokens; energy uses two-second power samples. These are not the same quantities as S1's arriving-request TTFT, ongoing-stream delivery gaps, and output-token throughput. The concrete opening is arrival-time interference under a pinned serving runtime, rather than another generic Orin feasibility or power sweep. This distinction follows their reported methodology; it is not proof that no other paper studies online edge serving. [Full text, sections 2–3](https://arxiv.org/html/2506.09554v2).

The arXiv record identifies this as an extended version of a PAISE 2025 short paper. Cite the version actually consulted; do not invent proceedings pages or an IEEE DOI. [Versioned record](https://arxiv.org/abs/2506.09554v2).

**S1's defensible intended contribution (our synthesis):** an experimentally explained, reproducible characterization of fixed prefill chunks on the stated Orin/runtime/model/workload combination. Two Orins can test repeatability within this platform class. They do not isolate shared-memory architecture versus a discrete GPU. Neither a positive effect nor a useful equivalence result is established yet. A noisy null must remain inconclusive, and a small-model result must remain bounded to that configuration.

## Pinned SGLang semantics

Source revision: `fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1`. Cite commit permalinks, and compare installed files/launch arguments before using these facts to explain a run.

The [server-argument declaration](https://github.com/sgl-project/sglang/blob/fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1/python/sglang/srt/server_args.py) defines `enable_mixed_chunk` as false by default. It is separate from `disable_overlap_schedule`, which concerns CPU-scheduler/GPU-worker overlap. `chunked_prefill_size` bounds a prefill chunk; `-1` disables chunking upstream. Thus CPU/GPU overlap, splitting prefills, and mixing prefill/decode in one batch are distinct settings. Runtime argument postprocessing and the local wrapper still need verification.

The [scheduler](https://github.com/sgl-project/sglang/blob/fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1/python/sglang/srt/managers/scheduler.py) makes `is_mixed_chunk` depend on both enabled chunking and `enable_mixed_chunk`. In `get_next_batch_to_run`, an available prefill batch takes precedence over a decode-only batch. The ongoing chunk is added again in `_get_new_batch_prefill_raw`; combining the running decode batch with new prefill is conditional on `is_mixed_chunk` and additional compatibility checks.

**Implication (source-based inference):** with mixed mode false, reducing chunk size does not guarantee a decode step between chunks. A long prefill can continue to postpone ongoing decoding over successive prefill iterations; smaller chunks can add overhead without removing that interruption. A default-mode study therefore characterizes this actual policy, not Sarathi-style stall-free service. Observe real timelines and runtime settings. If mixed mode is later enabled, record it as a deliberate protocol change before claim-bearing runs, rather than retrospectively relabeling data. Likewise, a chunk larger than every tested prompt is only a single-chunk control for those inputs.

## BibTeX-ready metadata

Metadata below follows the cited primary records. The SGLang entry deliberately identifies a source revision rather than guessing a release date.

```bibtex
@inproceedings{agrawal2024sarathi,
  author = {Amey Agrawal and Nitin Kedia and Ashish Panwar and Jayashree Mohan and Nipun Kwatra and Bhargav Gulavani and Alexey Tumanov and Ramachandran Ramjee},
  title = {Taming Throughput-Latency Tradeoff in {LLM} Inference with {Sarathi-Serve}},
  booktitle = {18th USENIX Symposium on Operating Systems Design and Implementation (OSDI 24)},
  year = {2024},
  month = jul,
  pages = {117--134},
  publisher = {USENIX Association},
  url = {https://www.usenix.org/conference/osdi24/presentation/agrawal}
}

@misc{arya2025edge,
  author = {Mayank Arya and Yogesh Simmhan},
  title = {Understanding the Performance and Power of {LLM} Inferencing on Edge Accelerators},
  year = {2025},
  eprint = {2506.09554},
  archivePrefix = {arXiv},
  primaryClass = {cs.DC},
  doi = {10.48550/arXiv.2506.09554},
  url = {https://arxiv.org/abs/2506.09554v2},
  note = {Version 2, June 12, 2025}
}

@misc{sglangPinned,
  author = {{SGLang Contributors}},
  title = {{SGLang} server arguments and scheduler},
  howpublished = {GitHub source code},
  url = {https://github.com/sgl-project/sglang/tree/fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1},
  note = {Revision fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1; accessed September 7, 2026}
}
```

Before finalizing related work, add only sources needed to support the eventual measured claim. This bounded review does not establish a comprehensive novelty search or authorize a “first” claim.
