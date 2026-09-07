# SRS manuscript

The methods/validation working draft compiles to two US-letter pages; repeated results and author details are pending. The target is the HiPC 2026 Student Research Symposium's two-page abstract, including references. See [verified submission requirements](../docs/RESEARCH.md) and [current project state](../PLAN.md).

The workstation build uses Tectonic 0.17.0, downloaded from its official release with pinned archive and executable SHA-256 checks. This follows the [official standalone installation method](https://tectonic-typesetting.github.io/book/latest/installation/). Tools and TeX caches stay in the ignored project cache. No serving dependencies or Orin host packages are required for typesetting.

Build the current working draft:

```bash
bash scripts/build-paper.sh
```

Build output goes to `paper/build/`. First use needs network access for TeX support files. Retain a verified final PDF separately under `paper/` when the manuscript is ready. The first PDF build is not itself evidence of submission readiness: page count, call-specific geometry, fonts, figures, citations, measurement claims, author details, advisor undertaking, and AI disclosure must be checked.

The call's one-inch margins take precedence over default IEEEtran dimensions in the working draft. Authentic author details are pending the user's response; an advisor signature will not be generated.
