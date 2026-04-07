# Media Porter Research

Updated: April 6, 2026

## Purpose

This document summarizes:

- what Media Porter currently is
- which similar applications exist in the market
- which capabilities those apps have that Media Porter does not yet have
- which features matter most if Media Porter is meant to become a paid product

This research combines:

- local repo analysis of the current Media Porter codebase
- public product information from official vendor sites

## Current State of Media Porter

Based on the codebase as of April 6, 2026:

- Media Porter is a Python 3.11 desktop app built with PySide6.
- The app already has a working scan -> inspect -> dedup -> import -> history workflow.
- Camera card detection, destination selection, folder rules, and a base GUI are implemented.
- The test suite currently passes: `73/73`.
- The project already contains partial support for config persistence, history, rules, and settings.

### Strengths already present

- camera-aware SD card scanning
- metadata-based folder organization
- atomic copy flow
- cancel support
- import history database
- settings dialog for rule templates
- cross-platform desktop direction
- solid automated test coverage for core modules

### Important gaps already identified in the repo

- source-card protection is not fully wired through the GUI flow
- duplicate filename handling is too filename-centric
- post-copy destination verification is not complete yet
- progress UI mixes overall and per-file progress
- true stop-and-resume is not implemented

## Similar Applications

### 1. OffShoot

Official site: <https://hedge.co/products/offshoot>

Positioning:

- fast, verified offload and ingest tool for video and media workflows
- strong focus on reliability, multiple destinations, and automation

Officially listed core capabilities:

- source and destination verification
- various checksum types
- stop and resume
- incremental backups
- advanced duplicate detection
- presets
- filter, rename, organize
- queuing
- simultaneous backups
- transfer logs

Officially listed Pro capabilities:

- ingest browser
- S3 destinations
- ASC MHL
- API and scripting
- iconik integration
- advanced presets
- helper app
- Connect Pro and webhooks

Official pricing shown on the product page on April 6, 2026:

- OffShoot: `$169` perpetual
- OffShoot Pro: `$249` perpetual
- OffShoot Pro rental: `$49` for 30 days

### 2. ShotPut Pro

Official site: <https://www.imagineproducts.com/product/shotput-pro/windows>

Positioning:

- verified offload tool for media professionals
- especially strong on reports and checksum-heavy workflows

Officially listed capabilities:

- verified offloads
- PDF media reports
- pause and resume
- checksum verification
- presets
- job history and reports
- duplicate detection
- ignore/copy by file extension
- queue automation
- ASC MHL
- Codex support

Official pricing shown on the product page on April 6, 2026:

- perpetual license: `$169`
- 30-day rental: `$60`

### 3. ProGrade Ingest Pro

Official site: <https://shop.progradedigital.com/products/ingest-pro-software>

Positioning:

- ingest, backup, and organization tool for photographers and videographers
- simpler than full DIT suites, but clearly aimed at safe transfer workflows

Officially listed capabilities:

- copies, backups, and archive workflows
- duplicate detection
- checksum creation
- metadata-based organization
- card health / refresh functions for supported ProGrade hardware

Official pricing shown on April 6, 2026:

- `$99.99` for a one-year license

### 4. Photo Mechanic

Official pricing/info page: <https://docs.camerabits.com/support/solutions/articles/48001252734-photo-mechanic-pricing-and-information>

Positioning:

- workflow tool for photographers
- broader than ingest alone: culling, metadata, renaming, and workflow speed

Officially described strengths:

- fast viewing and culling
- metadata editing
- file renaming and reorganization
- integration with existing post-processing workflows

Official pricing shown on April 6, 2026:

- `$14.99/month`
- `$149/year`
- `$299` perpetual

### 5. Lightroom Classic

Official page: <https://www.adobe.com/creativecloud/photography.html>

Positioning:

- not a dedicated offload app
- often used as the default import workflow by photographers

Why it matters:

- it is the most common "good enough" alternative
- many users will compare Media Porter to Lightroom import, even if Lightroom is not purpose-built for ingest verification

Official pricing shown on April 6, 2026:

- Lightroom plan: `$11.99/month`
- Photography plan: `$19.99/month`

### 6. Pomfort Offload Manager

Official site: <https://pomfort.com/offloadmanager/>

Positioning:

- secure backup and offload tool for on-set workflows
- more film/DIT oriented than photographer-oriented

Officially described strengths:

- secure and simple daily backups
- offload reports
- multiple copy jobs in parallel
- strong fit for productions that need more formal media handling

## What OffShoot Has That Media Porter Does Not Yet Have

This is the most relevant comparison because OffShoot is one of the clearest direct competitors.

### Verification and trust features

OffShoot has:

- source verification
- destination verification
- multiple checksum modes
- later re-verification through logs / media hash lists

Media Porter currently has:

- hash generation during copy
- basic import history
- no full destination re-hash verification pass yet
- no later re-verification workflow yet

### Recovery and continuation

OffShoot has:

- stop and resume
- incremental backups
- advanced duplicate detection designed for re-running jobs safely

Media Porter currently has:

- cancel support
- no persisted resume state
- dedup is still primarily filename + size based

### Multi-destination workflows

OffShoot has:

- simultaneous backups
- cascading destinations
- queueing and more advanced transfer orchestration

Media Porter currently has:

- one configured photo destination tree
- one configured video destination tree
- no second backup target
- no cascading flow
- no queueing

### Ingest workflow controls

OffShoot has:

- filter, rename, organize during ingest
- ingest browser for drilling into complex media sources
- labels and metadata prompts

Media Porter currently has:

- folder rule templates
- basic path configuration
- no rename rules during ingest
- no selective ingest browser
- no labels or workflow prompts

### Reporting and automation

OffShoot has:

- detailed transfer logs
- Connect notifications
- webhooks
- API and scripting
- helper app

Media Porter currently has:

- local import history
- no team notifications
- no automation API
- no external scripting hooks
- no helper app

### High-end workflow support

OffShoot Pro has:

- S3 destinations
- ASC MHL
- Codex / Alexa 35 support
- iconik integration

Media Porter currently does not have these capabilities.

## Gap Summary

If Media Porter wants to compete in the paid ingest-tool market, the biggest missing capabilities are:

1. full destination verification
2. stop-and-resume with persistent recovery state
3. stronger dedup and incremental backup behavior
4. dual-destination backup
5. transfer reports and richer audit trail
6. rename/filter workflow during ingest

These are more important than cosmetic improvements.

## What Media Porter Already Does Well

Media Porter is not starting from zero. It already has a good foundation for a niche pro ingest app:

- clean desktop UI
- camera-card aware scanning
- destination rules engine
- import history
- safety-oriented copy semantics
- strong tests

That foundation is enough to justify continuing, but not yet enough to charge confidently.

## Recommended Feature Priority

### Phase 1: Trust Foundation

Build first:

1. fix the source protection and duplicate identity bugs
2. add full destination verification
3. implement resume/recovery
4. add session reports

Why:

- these are trust features
- users will not pay for ingest software that feels unsafe or incomplete

### Phase 2: Paid V1

Build next:

1. dual-destination copy
2. stronger dedup against history and hashes
3. presets
4. searchable history
5. sidecar awareness

Why:

- these are the clearest time-saving upgrades over Finder, Explorer, and basic Lightroom import

### Phase 3: Pro Differentiation

Build later:

1. queueing
2. rename/filter controls
3. auto-ingest on card insert
4. retry failed files
5. conflict resolution UI
6. ingest browser

Why:

- these features make Media Porter feel like a real workflow tool, not just a copy utility

## Pricing Implication

The market clearly supports paid ingest tools.

Observed official pricing on April 6, 2026:

- OffShoot: `$169`
- OffShoot Pro: `$249`
- ShotPut Pro: `$169`
- ProGrade Ingest Pro: `$99.99/year`
- Photo Mechanic: `$149/year` or `$299` perpetual

This suggests Media Porter can likely charge if it delivers real trust and workflow value.

Recommended product split:

- Free: single destination, full verification, manual imports, basic history
- Pro: dual backup, presets, searchable history, richer reports, queueing, advanced workflow controls

Trust should not be paywalled. Workflow acceleration should be.

## Strategic Conclusion

Media Porter is best positioned as:

- a focused ingest and backup tool for photographers and small video teams
- safer and simpler than Finder/Explorer
- lighter and more approachable than full DIT suites

The clearest opportunity is not to beat every competitor at everything.

The clearest opportunity is to become:

- easier than OffShoot and ShotPut for small teams
- more trustworthy than generic file copy
- more focused on post-shoot ingest than Lightroom

## Sources

- OffShoot official product page: <https://hedge.co/products/offshoot>
- ShotPut Pro official product page: <https://www.imagineproducts.com/product/shotput-pro/windows>
- ShotPut Pro 2025 spec sheet: <https://www.imagineproducts.com/storage/544/ShotPut-Pro-Spec-Sheet-2025.pdf>
- ProGrade Ingest Pro official product page: <https://shop.progradedigital.com/products/ingest-pro-software>
- ProGrade software page: <https://shop.progradedigital.com/pages/software>
- Photo Mechanic pricing and information: <https://docs.camerabits.com/support/solutions/articles/48001252734-photo-mechanic-pricing-and-information>
- Adobe Photography plans: <https://www.adobe.com/creativecloud/photography.html>
- Pomfort Offload Manager: <https://pomfort.com/offloadmanager/>

