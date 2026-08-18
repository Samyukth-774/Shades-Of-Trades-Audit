# The Shades of Trades — Content Audit

An independent content and brand audit of the Instagram account
[@theshadesoftrades](https://www.instagram.com/theshadesoftrades/) (Apoorva Sharma, 524K followers),
built as a work sample.

**Live page → https://killcodex1.github.io/shades-of-trades-audit/**

## What it is

A single self-contained HTML page. No build step, no dependencies, no framework — open
`index.html` in any browser and it runs.

It covers six findings ranked by impact, a 30-day content plan, and a short section on what
the data made me take back from an earlier draft.

## Method

Every Instagram figure is measured, not estimated: **108 posts published between 7 February and
17 August 2026**, each with its real like, comment and play count, read from the public profile.

- No private data, no Insights access, no scraping of anything non-public
- Subject splits use a keyword classifier and are directional rather than conclusive
- Third-party engagement estimates appear only where explicitly labelled as such
- YouTube figures are included as a cross-check, not as primary evidence

The page states its own limits: the audit is an outside view, and the real picture in the
account's analytics may differ.

## Built with

Plain HTML, CSS and JavaScript in one file (~88KB). The animated background is a WebGL2 shader
ported from the React Bits `Scanner` component to raw WebGL — no React, no `ogl`. Charts, the
accordion gallery and the scroll-spy navigation are all hand-rolled.

Respects `prefers-reduced-motion`, works in light and dark, and prints cleanly.

## Author

Samyukth Bitra · samyukthbitra@gmail.com

---

*Nothing in this document is investment advice.*
