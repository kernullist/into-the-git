# Handoff Bundle: 멀티 Git 저장소 코드 분석 대시보드

Completeness: 98%
Domain: software
Output Type: dashboard

## How To Use This Export
- Give this full Handoff Markdown file to coding AI agents first.
- Start with Goal Brief for product context, then use Requirements and Technical Spec as the implementation contract.
- Treat AI Implementation Prompt as the execution section inside this bundle. Pass it alone only when the coding agent has very limited context.
- Use the Dashboard HTML export for human review, sharing, and status inspection, not as the primary coding-agent artifact.
- Treat remaining unknowns as explicit assumptions to resolve, not hidden requirements.

## Raw Intent
여러 Git 저장소의 코드를 AST 기반으로 분석하고, 오픈소스 정적 분석 도구를 통합하며, 사용자 피드백(전체 분석 결과에 대한 별점과 코멘트)을 우선으로 코드 개선 가능성을 제시하고, 자체 구현으로 Git 커밋 히스토리 기반 변경 빈도/목적 분석(클러스터링 후 지도 분류 전환 방식의 머신러닝 기반 목적 분류 포함)을 포함하는 웹 대시보드

## Goal Brief

Source kind: goal-brief

### Intent
여러 Git 저장소의 코드를 AST 기반으로 분석하고, 오픈소스 정적 분석 도구를 통합하며, 사용자 피드백(전체 분석 결과에 대한 별점과 코멘트)을 우선으로 코드 개선 가능성을 제시하고, 자체 구현으로 Git 커밋 히스토리 기반 변경 빈도/목적 분석(클러스터링 후 지도 분류 전환 방식의 머신러닝 기반 목적 분류 포함)을 포함하는 웹 대시보드

### Domain
software

### Target Users
개발자, 팀장

### Decisions
- 오픈소스 정적 분석 도구 최종 선정: C++ (cppcheck), Python (pylint, bandit), Java (PMD), JavaScript (ESLint)
- 사용자 피드백 수집 방식: 전체 분석 결과에 대해 별 5개 만점 평가(별점)와 코멘트 작성 가능
- 자체 구현 분석 기능: Git 커밋 히스토리에서 자주 수정되는 코드와 해당 커밋 메시지를 연계하여 변경 빈도 및 목적 파악
- 코드 스멜 규칙: 기본 제공 규칙만 우선 사용 (추후 사용자 정의 규칙은 필요한 경우 논의)
- 분석 중점 지표: 코드 복잡도, 중복 코드, 의존성, 사용자 피드백 점수(별점), 스멜 유형, 변경 빈도 및 목적
- 대시보드 레이아웃: 좌측 사이드바에 필터(저장소, 언어, 기간 등), 우측 메인 영역에서 지표별 시각화와 인라인 드릴다운 제공 (탭 대신 필터로 전환, 클릭 시 상세 정보 인라인 확장)
- 코드 개선 가능성 점수 산출: 별점(5점 만점)과 코멘트 감성 분석을 결합한 하이브리드 방식 (별점 70%, 감성 점수 30% 가중치, 감성 분석은 긍정/부정 키워드 기반 간단한 점수 사용)
- 개요 대시보드 유형: 하이브리드 개요 (핵심 지표 카드, 스멜/복잡도 트렌드 차트, 최신 사용자 피드백 코멘트 등 통합 제공)
- 분석 대상 Git 브랜치 선택: 사용자가 분석 대상 Git 브랜치를 직접 선택하는 방식
- 기본 필터 세트: 저장소, 언어, 기간 (추후 확장 가능)
- 기간 필터 UI 상세: 드롭다운으로 최근 1주, 최근 1개월, 최근 3개월, 직접 선택 제공, 기본값은 최근 1개월
- 커밋 메시지 목적 분류: 초기에는 비지도 클러스터링으로 자연스러운 패턴과 대표 카테고리를 도출하고, 이후 지도 분류기로 자동 분류하는 하이브리드 방식 (감성 분석은 기존 방식 유지)

### Open Assumptions
- 대규모 저장소 분석 최적화 전략
- 클러스터링 및 분류에 필요한 최적의 특징(feature)과 임계치
- 비지도 클러스터링에서 지도 분류기로의 전환 시점 및 기준

### Success Signal
- A future implementer can describe the target users, core workflow, required outputs, and implementation boundaries without reading the chat history.

### Handoff Readiness
- This document is a product brief, not the full implementation contract.
- Give the full [RefineGoals] Handoff - 멀티 Git 저장소 코드 분석 대시보드.md file to coding AI agents first.
- Use Technical Spec and AI Implementation Prompt as the core implementation sections inside that bundle.


---

## Requirements

Source kind: requirements

### Must Have
- GitHub, GitLab 등 멀티 Git 저장소 지원
- 파일 및 함수 단위 AST 분석
- 오픈소스 정적 분석 도구 통합 (cppcheck, pylint/bandit, PMD, ESLint)
- 코드 복잡도, 중복 코드, 의존성 분석
- 전체 분석 결과에 대한 사용자 별점(1~5) 및 코멘트 피드백
- 자동 코드 스멜 감지 (기본 규칙)
- Git 커밋 히스토리 기반 코드 변경 빈도 및 목적 분석 (자체 구현, 하이브리드 ML 분류 포함)

### Nice To Have
- 사용자 정의 스멜 규칙 지원 (향후)

### Constraints
- 지원 언어: C++, Python, Java, Node.js(JavaScript)
- 지원 플랫폼: GitHub, GitLab
- 분석 방법: AST + 오픈소스 정적 분석 도구 통합 + 자체 커밋 분석 + 머신러닝 기반 커밋 목적 분류 (클러스터링→지도 분류 하이브리드)
- 배포 환경: 별도 웹서버 (온프레미스)
- 비용: 오픈소스 도구 우선 사용
- 코드 스멜 규칙: 기본 제공 규칙만 우선 적용 (사용자 정의 규칙은 추후 검토)

### Unknowns
- 대규모 저장소 분석 최적화 전략
- 클러스터링 및 분류에 필요한 최적의 특징(feature)과 임계치
- 비지도 클러스터링에서 지도 분류기로의 전환 시점 및 기준

### Functional Acceptance Criteria
- GitHub, GitLab 등 멀티 Git 저장소 지원: provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- 파일 및 함수 단위 AST 분석: provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- 오픈소스 정적 분석 도구 통합 (cppcheck, pylint/bandit, PMD, ESLint): provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- 코드 복잡도, 중복 코드, 의존성 분석: provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- 전체 분석 결과에 대한 사용자 별점(1~5) 및 코멘트 피드백: provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- 자동 코드 스멜 감지 (기본 규칙): provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.
- Git 커밋 히스토리 기반 코드 변경 빈도 및 목적 분석 (자체 구현, 하이브리드 ML 분류 포함): provide a visible workflow or API entry point, persist or derive the required output, expose recoverable failure states, and cover the behavior with realistic test data.

### UX Acceptance Criteria
- The primary workflow must be visible without reading onboarding text.
- Dashboard users must be able to scan overall status first, then drill into repository, file, function, issue, and recommendation details.
- Long-running analysis work must show progress, partial status, cancellation or retry affordances, and clear completion/failure states.
- Filters, charts, and drilldowns must stay synchronized so users can understand why a code area was ranked as important.
- Exported reports must preserve enough context for a developer to act without reopening the dashboard.
- The export/dashboard area must explain which artifact is for human review and which Markdown handoff should be given to coding AI agents.

### Non-Goals
- No non-goals have been explicitly decided yet.

### Requirement Traceability Checklist
- [ ] Every must-have feature has a visible UI entry point or API behavior.
- [ ] Every generated metric, score, and recommendation can be traced back to source data.
- [ ] Every open question remains visible until answered or explicitly dismissed.
- [ ] Every external tool, repository, analysis, and storage failure has a user-visible fallback or error state.


---

## Technical Spec

Source kind: technical-spec

### Goal
여러 Git 저장소의 코드를 AST 기반으로 분석하고, 오픈소스 정적 분석 도구를 통합하며, 사용자 피드백(전체 분석 결과에 대한 별점과 코멘트)을 우선으로 코드 개선 가능성을 제시하고, 자체 구현으로 Git 커밋 히스토리 기반 변경 빈도/목적 분석(클러스터링 후 지도 분류 전환 방식의 머신러닝 기반 목적 분류 포함)을 포함하는 웹 대시보드

### Current Product Decision Summary
- 오픈소스 정적 분석 도구 최종 선정: C++ (cppcheck), Python (pylint, bandit), Java (PMD), JavaScript (ESLint)
- 사용자 피드백 수집 방식: 전체 분석 결과에 대해 별 5개 만점 평가(별점)와 코멘트 작성 가능
- 자체 구현 분석 기능: Git 커밋 히스토리에서 자주 수정되는 코드와 해당 커밋 메시지를 연계하여 변경 빈도 및 목적 파악
- 코드 스멜 규칙: 기본 제공 규칙만 우선 사용 (추후 사용자 정의 규칙은 필요한 경우 논의)
- 분석 중점 지표: 코드 복잡도, 중복 코드, 의존성, 사용자 피드백 점수(별점), 스멜 유형, 변경 빈도 및 목적
- 대시보드 레이아웃: 좌측 사이드바에 필터(저장소, 언어, 기간 등), 우측 메인 영역에서 지표별 시각화와 인라인 드릴다운 제공 (탭 대신 필터로 전환, 클릭 시 상세 정보 인라인 확장)
- 코드 개선 가능성 점수 산출: 별점(5점 만점)과 코멘트 감성 분석을 결합한 하이브리드 방식 (별점 70%, 감성 점수 30% 가중치, 감성 분석은 긍정/부정 키워드 기반 간단한 점수 사용)
- 개요 대시보드 유형: 하이브리드 개요 (핵심 지표 카드, 스멜/복잡도 트렌드 차트, 최신 사용자 피드백 코멘트 등 통합 제공)
- 분석 대상 Git 브랜치 선택: 사용자가 분석 대상 Git 브랜치를 직접 선택하는 방식
- 기본 필터 세트: 저장소, 언어, 기간 (추후 확장 가능)
- 기간 필터 UI 상세: 드롭다운으로 최근 1주, 최근 1개월, 최근 3개월, 직접 선택 제공, 기본값은 최근 1개월
- 커밋 메시지 목적 분류: 초기에는 비지도 클러스터링으로 자연스러운 패턴과 대표 카테고리를 도출하고, 이후 지도 분류기로 자동 분류하는 하이브리드 방식 (감성 분석은 기존 방식 유지)

### Recommended Architecture
- Web dashboard: on-premises web application with project setup, analysis run monitoring, overview metrics, filters, drilldowns, feedback, and report export.
- Source connector layer: GitHub and GitLab repository discovery, authentication, branch selection, clone/fetch, and commit metadata ingestion.
- Analysis orchestration layer: schedules repository analysis runs, isolates tool execution, tracks progress, captures logs, and supports retry/cancel.
- Analyzer adapter layer: normalizes cppcheck, pylint, bandit, PMD, ESLint, AST parsing, complexity, duplication, dependency, and custom smell outputs.
- Repository intelligence layer: correlates static findings with file/function ownership, commit frequency, commit messages, and change-purpose classification.
- Scoring layer: computes improvement priority from static findings, change history, user ratings, comment sentiment, recency, and configurable weights.
- Storage layer: persists repositories, branches, analysis runs, normalized findings, metrics, feedback, recommendations, and export snapshots.
- Reporting layer: generates dashboard views and downloadable implementation/report artifacts from the latest normalized data.

### Implementation Contract
- Treat confirmed decisions as requirements.
- Treat unknowns as unresolved assumptions that must be surfaced in the UI and documents.
- Do not silently implement a guessed answer for an unknown. Recommend a default and ask for confirmation.
- Preserve the on-premises deployment constraint unless a later decision explicitly requires SaaS/cloud behavior.
- Prefer open-source analyzers and transparent scoring rules before adding proprietary services.
- Keep analyzer adapters replaceable so tool upgrades or language additions do not rewrite the dashboard.
- A coding AI should stop and ask for clarification only when an unresolved item blocks architecture, data contracts, or scoring semantics and no recommended default is reasonable.

### Core Modules
- Project Manager: creates workspaces/projects and binds one or more GitHub/GitLab repositories.
- Repository Connector: handles credentials, branch selection, clone/fetch, commit history ingestion, and repository metadata refresh.
- Analysis Runner: executes static analyzers and AST/metric extraction in isolated jobs with progress and logs.
- Analyzer Adapters: one adapter per tool/language, each converting native output into a normalized finding schema.
- AST And Metric Engine: extracts file/function symbols, complexity, duplication, dependencies, and code ownership hints.
- Commit Intelligence Engine: computes change frequency and classifies commit purpose from commit messages and touched files.
- Scoring Engine: combines findings, complexity, duplication, dependencies, change history, ratings, and comment sentiment into improvement priority.
- Feedback Module: stores 1-5 star ratings and comments for whole analysis results, then feeds aggregate signals back into scoring.
- Dashboard UI: overview cards, trends, filters, drilldowns, inline details, and recommendation queues.
- Report Exporter: exports dashboard snapshots and actionable improvement reports.

### Data Model
- Project: id, name, description, createdAt, updatedAt.
- Repository: id, projectId, provider, remoteUrl, defaultBranch, selectedBranches, languageSummary, lastFetchedAt.
- AnalysisRun: id, projectId, repositoryIds, branchRefs, status, startedAt, finishedAt, progress, logs, toolVersions, errorSummary.
- SourceFile: id, repositoryId, path, language, size, hash, lastCommitSha, ownerHint.
- CodeSymbol: id, fileId, kind, name, location, signature, complexity, dependencyRefs.
- Finding: id, runId, repositoryId, fileId, symbolId, tool, ruleId, severity, category, message, location, fingerprint, rawPayload.
- MetricSnapshot: id, runId, scopeType, scopeId, metricName, value, unit.
- CommitSignal: id, repositoryId, fileId, symbolId, commitSha, author, committedAt, purposeCategory, message, touchedLines.
- Feedback: id, runId, rating, comment, sentimentScore, createdAt.
- Recommendation: id, runId, targetType, targetId, priorityScore, rationale, contributingSignals, status.
- ExportReport: id, runId, title, format, content, createdAt.

### State Transitions
1. Project setup: user creates a project and connects GitHub/GitLab repositories.
2. Branch selection: user selects target branches and time range filters.
3. Analysis run queued: system records an AnalysisRun and schedules repository fetch plus analyzer jobs.
4. Repository ingestion: connector fetches source, commit metadata, and branch refs.
5. Static/AST analysis: adapters execute tools and emit normalized findings, symbols, metrics, and logs.
6. Commit intelligence: system computes change frequency and purpose categories for files/functions.
7. Scoring: system combines static findings, metrics, history, ratings, and comment sentiment into recommendations.
8. Dashboard publication: overview cards, charts, filters, and inline drilldowns refresh from the completed run.
9. Feedback loop: user submits rating/comment; scoring and trend displays update.
10. Export: user downloads a report with findings, rationale, recommendations, and run metadata.

### API Surface
- GET /api/projects, POST /api/projects
- GET /api/projects/:projectId/repositories, POST /api/projects/:projectId/repositories
- GET /api/repositories/:repositoryId/branches
- POST /api/analysis-runs, GET /api/analysis-runs/:runId, POST /api/analysis-runs/:runId/cancel, POST /api/analysis-runs/:runId/retry
- GET /api/analysis-runs/:runId/findings
- GET /api/analysis-runs/:runId/metrics
- GET /api/analysis-runs/:runId/recommendations
- POST /api/analysis-runs/:runId/feedback
- GET /api/analysis-runs/:runId/export

### Primary UX Flow
1. User creates a project and connects GitHub/GitLab repositories.
2. User selects branches and analysis period, with recent 1 month as the default period.
3. User starts analysis and monitors per-repository progress, tool logs, and failures.
4. Dashboard shows overview cards, smell/complexity trends, feedback summaries, and high-priority improvement targets.
5. User filters by repository, language, period, severity, smell type, and priority.
6. User clicks a metric or recommendation to expand inline file/function details and contributing signals.
7. User rates the full analysis result and adds a comment.
8. System recalculates improvement priority and exports an actionable report.

### Error And Fallback Behavior
- Repository authentication or fetch failure: mark the repository failed, keep other repositories running, and expose retry with credential diagnostics.
- Analyzer executable missing or exits non-zero: show tool-specific setup/log output and preserve raw logs for troubleshooting.
- AST parse failure for a file: record a per-file parse error and continue analyzing other files.
- Large repository timeout: checkpoint partial results, show skipped scopes, and recommend narrower branch/period filters.
- ML purpose classifier unavailable: fall back to rule-based commit message categories and label the result as lower confidence.
- Feedback sentiment scoring unavailable: use star rating only and preserve comments for later recomputation.
- Export failure: keep the completed run intact and allow retry without rerunning analysis.

### Goal Clarity Gate
- Implementation-ready: completenessScore is about 85 or higher and remaining unknowns are non-blocking.
- Planning-ready: completenessScore is about 60 to 84; continue asking one high-leverage question or offering a recommended default.
- Not ready: completenessScore is below 60 or target users, core workflow, required outputs, constraints, and success criteria are still unclear.
- A coding AI should be able to implement from the full Handoff Markdown bundle, especially Technical Spec and AI Implementation Prompt, without reading the chat transcript before the goal is treated as clear.
- When implementation-ready, show a ready banner with dashboard inspection, full dashboard HTML export, and an AI-agent Markdown handoff export named from the current session title.

### Security And Privacy Notes
- Repository credentials and access tokens must be encrypted at rest and never exposed to the browser after setup.
- Checked-out source code, analyzer logs, commit messages, and findings may contain sensitive intellectual property.
- Analyzer execution should run with least privilege, bounded CPU/memory/time limits, and isolated working directories.
- Exported reports may include file paths, commit metadata, comments, and code snippets; require explicit download action.
- Tool licenses and transitive dependencies must be reviewed before bundling or redistributing analyzers.

### Implementation Constraints
- 지원 언어: C++, Python, Java, Node.js(JavaScript)
- 지원 플랫폼: GitHub, GitLab
- 분석 방법: AST + 오픈소스 정적 분석 도구 통합 + 자체 커밋 분석 + 머신러닝 기반 커밋 목적 분류 (클러스터링→지도 분류 하이브리드)
- 배포 환경: 별도 웹서버 (온프레미스)
- 비용: 오픈소스 도구 우선 사용
- 코드 스멜 규칙: 기본 제공 규칙만 우선 적용 (사용자 정의 규칙은 추후 검토)

### Product Risks
- 오픈소스 도구의 라이선스 호환성 및 유지보수 의존성
- 다양한 언어/도구 간 분석 결과 통합 및 일관성 확보 어려움
- 사용자 피드백이 주관적일 수 있으나 전체 만족도로 추상화하여 개선 가능성 점수에 반영 필요
- 분석 결과 시각화가 사용자 요구에 부합하지 않을 가능성
- cppcheck의 거짓 양성(false positive)으로 인한 노이즈 가능성
- 커밋 분석 시 대규모 저장소에서 성능 저하 및 저장 공간 부담
- ML 모델 학습 및 배포 추가 복잡성 (데이터 수집, 카테고리 라벨링, 학습 파이프라인 구축, 모델 서빙 필요)
- 클러스터링으로 도출된 카테고리가 불명확하거나 과도하게 세분화되어 실용성이 떨어질 가능성

### Reference Inputs
- 코드 스멜 감지 기준: SonarQube, PMD 등 기존 규칙 참고
- 참고: GitLab과 정적 분석기 통합 관련 논의 (Reddit)
- 후보 도구: cppcheck (C++), pylint/bandit (Python), PMD/SpotBugs (Java), ESLint (JavaScript)
- C++ 정적 분석 도구 추천: cppcheck (Reddit, Netmarble 기술 블로그 등)
- 사용자 피드백 집계 방식: 평균 별점, 최신 코멘트 표시 (일반적 UX 패턴)

### Testing Strategy
- Unit test analyzer output normalization, scoring formulas, filter logic, and commit-purpose classification.
- Integration test GitHub/GitLab repository ingestion with fixture repositories.
- Integration test each analyzer adapter with known vulnerable/smelly sample code.
- API test project setup, repository branch discovery, analysis run lifecycle, findings, feedback, recommendations, and export.
- UI test dashboard filters, inline drilldowns, progress/failure states, feedback submission, and report download.
- Performance test large repository ingestion, incremental reruns, and multi-repository analysis.

### Test Matrix
- [ ] Connect one GitHub repository and one GitLab repository.
- [ ] Discover branches and run analysis on a selected branch.
- [ ] Run C++, Python, Java, and JavaScript analyzer adapters against fixture projects.
- [ ] Normalize analyzer findings into one shared finding schema.
- [ ] Compute complexity, duplication, dependency, and change-frequency metrics.
- [ ] Classify commit purpose with ML path and rule-based fallback.
- [ ] Filter dashboard by repository, language, and period.
- [ ] Open inline drilldown from overview metric to file/function details.
- [ ] Submit 1-5 star rating and comment, then verify scoring updates.
- [ ] Export an actionable report from a completed analysis run.
- [ ] Retry a failed repository fetch or analyzer job without losing completed results.


---

## AI Implementation Prompt

Source kind: ai-implementation-prompt

Build the following goal with production-quality implementation.

### Goal
여러 Git 저장소의 코드를 AST 기반으로 분석하고, 오픈소스 정적 분석 도구를 통합하며, 사용자 피드백(전체 분석 결과에 대한 별점과 코멘트)을 우선으로 코드 개선 가능성을 제시하고, 자체 구현으로 Git 커밋 히스토리 기반 변경 빈도/목적 분석(클러스터링 후 지도 분류 전환 방식의 머신러닝 기반 목적 분류 포함)을 포함하는 웹 대시보드

### Context For The Implementing AI
You only have this document or the larger RefineGoals handoff bundle that contains it. Do not assume access to the original conversation. Treat every unresolved or not-specified item as an explicit gap to resolve before implementation. Preserve confirmed decisions and do not silently convert unknowns into requirements.

### Implementation Mission
Build the smallest production-quality version that satisfies the confirmed goal state while keeping unresolved assumptions visible. Prefer a complete, reliable local MVP over a broad but shallow prototype.

### Required Features
- GitHub, GitLab 등 멀티 Git 저장소 지원
- 파일 및 함수 단위 AST 분석
- 오픈소스 정적 분석 도구 통합 (cppcheck, pylint/bandit, PMD, ESLint)
- 코드 복잡도, 중복 코드, 의존성 분석
- 전체 분석 결과에 대한 사용자 별점(1~5) 및 코멘트 피드백
- 자동 코드 스멜 감지 (기본 규칙)
- Git 커밋 히스토리 기반 코드 변경 빈도 및 목적 분석 (자체 구현, 하이브리드 ML 분류 포함)

### Recommended Build Order
1. Resolve blocking open questions or apply documented defaults for large-repository optimization and commit-purpose taxonomy.
2. Scaffold the on-premises web app, database, background worker, and analyzer execution environment.
3. Implement project, repository, branch, analysis-run, finding, metric, feedback, recommendation, and export data models.
4. Build GitHub/GitLab connectors with branch selection, clone/fetch, credential handling, and commit metadata ingestion.
5. Implement analyzer adapters for the selected languages and normalize all tool outputs into one finding schema.
6. Implement AST/metric extraction, duplication/dependency analysis, commit-frequency analysis, and purpose classification.
7. Implement priority scoring from findings, metrics, history, ratings, and comment sentiment.
8. Build the dashboard overview, filters, charts, inline drilldowns, feedback form, and report export.
9. Add unit, integration, UI, and performance tests using fixture repositories.

### Expected Screens Or Views
- Project list and project creation.
- Repository connection/setup with GitHub/GitLab provider, credentials, repository URL, and branch selection.
- Analysis run monitor with per-repository status, logs, retry/cancel, and progress.
- Overview dashboard with metric cards, smell/complexity trends, feedback summary, and top improvement targets.
- Filter sidebar for repository, language, period, severity, smell type, and priority.
- Inline drilldown panel for file/function findings, commit history, contributing signals, and recommendation rationale.
- Feedback form for 1-5 star rating and comments on the complete analysis result.
- Export/report view for completed runs, including a short guide that tells users which export is for human review and which Markdown file should be handed to coding AI agents.

### Suggested File/Module Boundaries
- connectors/: GitHub/GitLab repository access, branch discovery, clone/fetch, and commit metadata ingestion.
- analysis/: analysis run orchestration, job queue, worker lifecycle, cancellation, retry, and logs.
- analyzers/: cppcheck, pylint, bandit, PMD, ESLint, AST, complexity, duplication, and dependency adapters.
- normalization/: common finding, metric, symbol, and commit-signal schemas.
- scoring/: priority score, feedback score, sentiment score, and recommendation rationale.
- storage/: database schema, migrations, repositories, and report snapshots.
- api/: project, repository, branch, analysis-run, finding, metric, feedback, recommendation, and export endpoints.
- ui/: setup forms, run monitor, dashboard filters, charts, drilldowns, feedback, and export controls.

### Data And API Requirements
- Persist repositories, selected branches, analysis runs, tool versions, findings, metrics, feedback, recommendations, and exports.
- Store raw analyzer payloads enough for debugging, but render users through the normalized schema.
- Use stable fingerprints for findings so reruns can track resolved, recurring, and newly introduced issues.
- Keep source code checkout paths and credentials server-side.
- API responses must support pagination/filtering for large repositories and many findings.

### Implementation Rules
- Analyzer adapters must be replaceable and independently testable.
- Run external analyzers in isolated working directories with explicit timeouts and captured stdout/stderr.
- Treat ML commit-purpose classification as pluggable; provide a rule-based fallback until training data and categories are finalized.
- Every score shown in the UI must expose contributing signals so users can understand why a file/function was prioritized.
- Keep user feedback at the analysis-result level unless later requirements introduce finding-level feedback.
- Keep the default smell rules built in; user-defined rules are a later extension.

### Constraints
- 지원 언어: C++, Python, Java, Node.js(JavaScript)
- 지원 플랫폼: GitHub, GitLab
- 분석 방법: AST + 오픈소스 정적 분석 도구 통합 + 자체 커밋 분석 + 머신러닝 기반 커밋 목적 분류 (클러스터링→지도 분류 하이브리드)
- 배포 환경: 별도 웹서버 (온프레미스)
- 비용: 오픈소스 도구 우선 사용
- 코드 스멜 규칙: 기본 제공 규칙만 우선 적용 (사용자 정의 규칙은 추후 검토)

### Decisions Already Made
- 오픈소스 정적 분석 도구 최종 선정: C++ (cppcheck), Python (pylint, bandit), Java (PMD), JavaScript (ESLint)
- 사용자 피드백 수집 방식: 전체 분석 결과에 대해 별 5개 만점 평가(별점)와 코멘트 작성 가능
- 자체 구현 분석 기능: Git 커밋 히스토리에서 자주 수정되는 코드와 해당 커밋 메시지를 연계하여 변경 빈도 및 목적 파악
- 코드 스멜 규칙: 기본 제공 규칙만 우선 사용 (추후 사용자 정의 규칙은 필요한 경우 논의)
- 분석 중점 지표: 코드 복잡도, 중복 코드, 의존성, 사용자 피드백 점수(별점), 스멜 유형, 변경 빈도 및 목적
- 대시보드 레이아웃: 좌측 사이드바에 필터(저장소, 언어, 기간 등), 우측 메인 영역에서 지표별 시각화와 인라인 드릴다운 제공 (탭 대신 필터로 전환, 클릭 시 상세 정보 인라인 확장)
- 코드 개선 가능성 점수 산출: 별점(5점 만점)과 코멘트 감성 분석을 결합한 하이브리드 방식 (별점 70%, 감성 점수 30% 가중치, 감성 분석은 긍정/부정 키워드 기반 간단한 점수 사용)
- 개요 대시보드 유형: 하이브리드 개요 (핵심 지표 카드, 스멜/복잡도 트렌드 차트, 최신 사용자 피드백 코멘트 등 통합 제공)
- 분석 대상 Git 브랜치 선택: 사용자가 분석 대상 Git 브랜치를 직접 선택하는 방식
- 기본 필터 세트: 저장소, 언어, 기간 (추후 확장 가능)
- 기간 필터 UI 상세: 드롭다운으로 최근 1주, 최근 1개월, 최근 3개월, 직접 선택 제공, 기본값은 최근 1개월
- 커밋 메시지 목적 분류: 초기에는 비지도 클러스터링으로 자연스러운 패턴과 대표 카테고리를 도출하고, 이후 지도 분류기로 자동 분류하는 하이브리드 방식 (감성 분석은 기존 방식 유지)

### Open Questions
- 대규모 저장소 분석 최적화 전략
- 클러스터링 및 분류에 필요한 최적의 특징(feature)과 임계치
- 비지도 클러스터링에서 지도 분류기로의 전환 시점 및 기준

### Risks To Handle
- 오픈소스 도구의 라이선스 호환성 및 유지보수 의존성
- 다양한 언어/도구 간 분석 결과 통합 및 일관성 확보 어려움
- 사용자 피드백이 주관적일 수 있으나 전체 만족도로 추상화하여 개선 가능성 점수에 반영 필요
- 분석 결과 시각화가 사용자 요구에 부합하지 않을 가능성
- cppcheck의 거짓 양성(false positive)으로 인한 노이즈 가능성
- 커밋 분석 시 대규모 저장소에서 성능 저하 및 저장 공간 부담
- ML 모델 학습 및 배포 추가 복잡성 (데이터 수집, 카테고리 라벨링, 학습 파이프라인 구축, 모델 서빙 필요)
- 클러스터링으로 도출된 카테고리가 불명확하거나 과도하게 세분화되어 실용성이 떨어질 가능성

### Definition Of Done
- A new developer or AI model can implement the product from this document without needing the chat transcript.
- The primary workflow works end to end from repository connection to completed analysis, dashboard review, feedback, and export.
- At least one fixture repository per supported language can be analyzed successfully.
- Analyzer failures, repository failures, timeouts, and partial results are recoverable and visible.
- Dashboard metrics and recommendation scores are traceable to stored findings, metrics, history, and feedback.
- Generated/exported reports are readable, downloadable, and aligned with the current analysis run.

### Final Implementation Checklist
- [ ] No required workflow is represented only as temporary stub text.
- [ ] All analysis runs and findings survive page refresh and server restart.
- [ ] Repository credentials are protected and never rendered back to the browser.
- [ ] Each analyzer adapter has fixture-based tests.
- [ ] Large result sets remain usable through pagination, filtering, or aggregation.
- [ ] Scores and recommendations show their contributing signals.
- [ ] Failed repositories or analyzers can be retried without rerunning successful work.
- [ ] Exported reports can be read independently from the dashboard.
- [ ] README matches the implemented setup and behavior.
