# Multi-Git Repository Code Analysis Dashboard

여러 Git 저장소의 코드를 AST 기반으로 분석하고, 오픈소스 정적 분석 도구를 통합하며, 사용자 피드백(별점 + 코멘트)을 반영한 코드 개선 가능성을 제시하는 온프레미스 웹 대시보드입니다.

## Features

- **멀티 저장소 지원**: GitHub, GitLab, 로컬 Git 저장소 연결
- **정적 분석 통합**: cppcheck (C++), pylint + bandit (Python), PMD (Java), ESLint (JavaScript)
- **AST 기반 분석**: 파일/함수/클래스 단위 심볼 추출, 복잡도, 의존성 분석
- **코드 메트릭**: Cyclomatic Complexity, Maintainability Index, 코드 중복, Fan-in/Fan-out
- **커밋 인텔리전스**: 변경 빈도 분석 + ML 기반 커밋 목적 분류 (비지도 KMeans → 지도 Naive Bayes 하이브리드)
- **사용자 피드백**: 전체 분석 결과에 대한 별점(1~5) 및 코멘트, 감성 분석
- **우선순위 점수**: 정적 발견사항(35%) + 복잡도(20%) + 중복(10%) + 의존성(10%) + 변경빈도(15%) + 피드백(10%)
- **인터랙티브 대시보드**: 지표 카드, 심각도/스멜/복잡도 차트, 커밋 목적 분포, Top 개선 대상
- **필터**: 저장소, 언어, 기간(1주/1개월/3개월/직접지정), 심각도, 스멜 유형, 우선순위
- **인라인 드릴다운**: 추천 항목 클릭 시 파일/함수 상세 findings, 심볼, 커밋 내역 표시
- **리포트 익스포트**: Markdown (AI 에이전트 핸드오프용) + JSON (도구 연동용)

---

## Prerequisites

### 필수

| 요구사항 | 버전 | 확인 |
|----------|------|------|
| Python | 3.9 이상 | `python --version` |
| Git | 2.20 이상 | `git --version` |
| pip | 최신 | `python -m pip install --upgrade pip` |

### 외부 분석 도구 (선택 - 없으면 내장 AST 분석만 동작)

외부 정적 분석 도구를 설치하지 않아도 대시보드는 정상 작동합니다. 도구가 없으면 해당 언어는 내장 AST 분석 + 복잡도 측정만 수행하고 정적 분석 findings는 건너뜁니다.

#### Windows

```powershell
# C++ (cppcheck)
winget install cppcheck

# Python (pylint, bandit)
pip install pylint bandit

# Java (PMD) - https://pmd.github.io 에서 pmd-bin-*.zip 다운로드 후 PATH 등록
# 또는 scoop install pmd

# JavaScript (ESLint)
npm install -g eslint
```

#### macOS

```bash
# C++
brew install cppcheck

# Python
pip3 install pylint bandit

# Java
brew install pmd

# JavaScript
npm install -g eslint
```

#### Linux (Ubuntu/Debian)

```bash
# C++
sudo apt install cppcheck

# Python
pip install pylint bandit

# Java - https://pmd.github.io 에서 다운로드
# JavaScript
npm install -g eslint
```

---

## Quick Start

### 1. 프로젝트 클론 및 가상환경 설정

```bash
git clone <repository-url>
cd into-the-git

# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

`requirements.txt`에 포함된 주요 패키지:
- **Flask** + Flask-SQLAlchemy + Flask-CORS: 웹 프레임워크 및 ORM
- **GitPython**: Git 저장소 조작
- **scikit-learn** + numpy + scipy: ML 분류 (KMeans, Naive Bayes)
- **radon**: Python 복잡도 메트릭
- **tree-sitter**: 다중 언어 AST 파싱
- **gunicorn**: 프로덕션 WSGI 서버

### 3. 환경변수 설정 (선택)

```bash
# .env 파일 생성 (Windows)
echo GITHUB_TOKEN=ghp_your_token_here > .env
echo GITLAB_TOKEN=glpat_your_token_here >> .env

# .env 파일 생성 (macOS/Linux)
cat > .env << EOF
GITHUB_TOKEN=ghp_your_token_here
GITLAB_TOKEN=glpat_your_token_here
FLASK_DEBUG=1
EOF
```

환경변수 목록:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SECRET_KEY` | 랜덤 생성 | Flask 세션 암호화 키 |
| `DATABASE_URL` | `sqlite:///data/dashboard.db` | DB 연결 문자열 |
| `GITHUB_TOKEN` | 없음 | GitHub Personal Access Token |
| `GITLAB_TOKEN` | 없음 | GitLab Personal Access Token |
| `FLASK_DEBUG` | `0` | 디버그 모드 (`1` = 활성화) |
| `MAX_ANALYSIS_TIMEOUT` | `3600` | 분석 최대 시간(초) |
| `WORKER_THREADS` | `2` | 백그라운드 워커 스레드 수 |
| `CLUSTER_MIN_SAMPLES` | `30` | ML 클러스터링 최소 샘플 수 |
| `CLASSIFIER_CONFIDENCE_THRESHOLD` | `0.6` | 지도 분류기 신뢰도 임계값 |

### 4. 실행

```bash
# 개발 서버
python app.py
```

브라우저에서 **http://localhost:5000** 으로 접속합니다.

### 5. 설치 확인

```bash
# 모든 테스트 실행
python -m unittest discover tests -v

# 55 tests OK 가 출력되면 정상
```

---

## 사용 가이드

### 전체 워크플로우

```
Project 생성 → Repository 연결 → Branch 선택 → 분석 실행 → 대시보드 검토 → 피드백 → 리포트 Export
```

### 1. Project 생성

1. 메인 페이지에서 **"+ New Project"** 클릭
2. Project 이름과 설명 입력
3. **"Create Project"** 클릭

### 2. Repository 연결

Project 페이지에서 **"+ Add Repository"** 클릭:

| Provider | URL 예시 | 토큰 필요 |
|----------|---------|:--------:|
| Local Path | `C:\Projects\my-repo` 또는 `/home/user/my-repo` | 아니오 |
| GitHub | `https://github.com/user/repo.git` | 권장 |
| GitLab | `https://gitlab.com/user/repo.git` | 권장 |

### 3. Branch 선택

1. Repository 카드에서 **"Select Branch"** 클릭
2. 분석할 Branch 선택 (드롭다운에서 자동 조회)
3. 분석 기간 선택: 기본값 **Last 1 Month**
   - Last 1 Week / Last 1 Month / Last 3 Months / Custom (날짜 직접 지정)
4. **"Confirm & Analyze"** 클릭

### 4. 분석 실행 및 모니터링

- Project 페이지에서 **"Run Analysis"** 클릭
- 분석 실행 페이지에서 **실시간 로그**, **진행률**, **상태** 확인
- 실행 중인 작업은 **Cancel** 가능
- 실패한 작업은 **Retry** 가능 (성공한 저장소 결과 보존)

### 5. 대시보드 검토

대시보드 화면 구성:
- **상단**: 6개 지표 카드 (Findings, Recommendations, Avg Rating, Feedbacks, Complexity, Changes)
- **중단 좌측**: Findings by Severity (막대 차트), Top Functions by Complexity (수평 막대)
- **중단 우측**: Code Smell Distribution (도넛 차트), Commit Purpose Distribution (도넛 차트)
- **하단 좌측**: Top Improvement Targets (우선순위 순 추천 목록)
- **하단 우측**: Recent Feedback (최신 피드백 코멘트)
- **최하단**: 별점 + 코멘트 피드백 제출 폼

### 6. 필터 사용

좌측 사이드바에서 필터 적용:
- **Project**: 프로젝트 선택
- **Repository**: 저장소별 필터
- **Language**: Python / JavaScript / Java / C++
- **Period**: 1주 / 1개월 / 3개월
- **Severity**: Critical / Major / Minor / Info
- **Smell Type**: 분석 실행 시 발견된 카테고리 기준 동적 생성
- **Priority**: High (75+) / Medium (50-74) / Low (<50)

### 7. 드릴다운

추천 목록의 항목을 클릭하면 우측 패널에 상세 정보 표시:
- **Contributing Signals**: 각 신호별 점수와 가중치
- **Findings**: 파일별 정적 분석 발견사항 (도구, 규칙, 심각도)
- **Symbols**: 함수/클래스 목록, 복잡도, 라인 위치
- **Commit History**: 해당 파일의 최근 커밋 내역 (작성자, 목적, 메시지)

### 8. 피드백 제출

대시보드 하단에서:
1. 별점 1~5 선택 (클릭)
2. 코멘트 작성 (한국어/영어 모두 지원)
3. **"Submit Feedback"** 클릭

제출 시:
- 감성 점수 자동 계산 (긍정/부정 키워드 기반)
- 모든 추천 항목의 feedback_score 재계산
- 대시보드 지표 자동 갱신

### 9. 리포트 익스포트

1. 분석 완료 후 **"Export Report"** 클릭
2. Format 선택:
   - **Markdown**: AI 코딩 에이전트에게 전달할 핸드오프 문서
   - **JSON**: 자동화 도구/API 연동용 기계 판독 형식
3. **"Generate Export"** → **"Download"** 클릭

---

## API Reference

### Projects

```bash
# 프로젝트 목록
curl http://localhost:5000/api/projects

# 프로젝트 생성
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "프로젝트 설명"}'

# 프로젝트 삭제
curl -X DELETE http://localhost:5000/api/projects/1
```

### Repositories

```bash
# 저장소 추가
curl -X POST http://localhost:5000/api/projects/1/repositories \
  -H "Content-Type: application/json" \
  -d '{"provider": "local", "remote_url": "/path/to/repo", "default_branch": "main"}'

# 저장소 브랜치 조회
curl http://localhost:5000/api/repositories/1/branches

# 저장소 정보 수정 (브랜치 선택)
curl -X PUT http://localhost:5000/api/repositories/1 \
  -H "Content-Type: application/json" \
  -d '{"selected_branches": ["main"], "default_branch": "main"}'
```

### Analysis Runs

```bash
# 분석 실행
curl -X POST http://localhost:5000/api/analysis-runs \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "repository_ids": [1], "period": "1m"}'

# 실행 상태 확인
curl http://localhost:5000/api/analysis-runs/1

# 실행 취소
curl -X POST http://localhost:5000/api/analysis-runs/1/cancel

# 실패한 저장소만 재시도
curl -X POST http://localhost:5000/api/analysis-runs/1/retry \
  -H "Content-Type: application/json" \
  -d '{"repository_ids": [1], "period": "1m"}'
```

### Findings & Metrics

```bash
# 발견사항 조회 (페이징 + 필터)
curl "http://localhost:5000/api/analysis-runs/1/findings?page=1&per_page=50&severity=critical&repository_id=1"

# 발견사항 요약
curl http://localhost:5000/api/analysis-runs/1/findings/summary

# 메트릭 조회
curl http://localhost:5000/api/analysis-runs/1/metrics

# 추천 목록
curl http://localhost:5000/api/analysis-runs/1/recommendations
```

### Dashboard & Details

```bash
# 대시보드 개요 (필터 포함)
curl "http://localhost:5000/api/dashboard/overview?project_id=1&repository_id=1&severity=critical&period=1m"

# 파일 상세 (드릴다운)
curl "http://localhost:5000/api/analysis-runs/1/files/src/main.py"

# 복잡도 트렌드
curl http://localhost:5000/api/analysis-runs/1/complexity-trend
```

### Feedback & Export

```bash
# 피드백 제출
curl -X POST http://localhost:5000/api/analysis-runs/1/feedback \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "comment": "분석 결과가 매우 유용합니다"}'

# 피드백 조회
curl http://localhost:5000/api/analysis-runs/1/feedback

# 리포트 익스포트 (Markdown)
curl "http://localhost:5000/api/analysis-runs/1/export?format=markdown"

# 리포트 익스포트 (JSON)
curl "http://localhost:5000/api/analysis-runs/1/export?format=json"

# 익스포트 다운로드
curl -O http://localhost:5000/api/exports/1/download
```

---

## Architecture

```
into-the-git/
├── app.py                     # Flask 애플리케이션 진입점
├── config.py                  # 설정 (환경변수, DB 경로, 토큰)
├── database.py                # SQLAlchemy 초기화
├── models.py                  # 11개 엔티티 데이터 모델
├── requirements.txt           # Python 의존성
│
├── connectors/                # Git 저장소 커넥터
│   ├── base.py                #   추상 베이스 클래스
│   ├── local.py               #   로컬 Git (clone/fetch/branch/commit)
│   ├── github.py              #   GitHub (토큰 인증)
│   └── gitlab.py              #   GitLab (토큰 인증)
│
├── analysis/                  # 분석 오케스트레이션
│   └── runner.py              #   분석 실행기 (ThreadPoolExecutor, timeout, 로그)
│
├── analyzers/                 # 정적 분석 어댑터 + AST 엔진
│   ├── base.py                #   어댑터 베이스 (subprocess 실행, timeout)
│   ├── adapters.py            #   cppcheck / pylint / bandit / PMD / ESLint
│   ├── ast_engine.py          #   다중 언어 AST 파싱 (Python ast + 정규식)
│   ├── complexity.py          #   Cyclomatic Complexity, MI (radon + 자체)
│   ├── duplication.py         #   코드 블록 중복 탐지 (해시 기반)
│   └── dependency.py          #   Import/Include 의존성 분석
│
├── commit_intel/              # 커밋 인텔리전스
│   ├── frequency.py           #   변경 빈도 계산
│   └── classifier.py          #   ML 커밋 목적 분류 (KMeans → NaiveBayes)
│
├── scoring/                   # 점수 엔진
│   ├── engine.py              #   우선순위 점수, 추천 생성
│   └── sentiment.py           #   감성 분석 (한/영 키워드)
│
├── normalization/             # 정규화 스키마
│   └── schemas.py             #   Finding/Metric/CommitSignal 정규화 함수
│
├── api/                       # REST API
│   └── routes.py              #   Flask Blueprint (16+ 엔드포인트)
│
├── templates/                 # Jinja2 HTML 템플릿
│   ├── base.html              #   공통 레이아웃 (사이드바 + Chart.js CDN)
│   ├── index.html             #   프로젝트 목록 + 생성
│   ├── project.html           #   저장소 연결 + 브랜치/기간 선택
│   ├── analysis.html          #   분석 실행 모니터링
│   ├── dashboard.html         #   메인 대시보드 (차트, 필터, 드릴다운)
│   └── export.html            #   리포트 익스포트
│
├── static/                    # 정적 파일
│   ├── css/style.css          #   스타일시트
│   └── js/dashboard.js        #   공통 유틸리티 함수
│
├── tests/                     # 테스트
│   ├── test_core.py           #   55개 단위/통합 테스트
│   └── fixtures/              #   언어별 샘플 코드
│       ├── sample.py
│       ├── sample.java
│       ├── sample.js
│       └── sample.cpp
│
└── data/                      # 런타임 데이터 (자동 생성)
    ├── dashboard.db           #   SQLite 데이터베이스
    ├── repos/                 #   클론된 저장소
    └── reports/               #   익스포트된 리포트
```

### 데이터 모델 (11개 엔티티)

| 엔티티 | 주요 필드 | 관계 |
|--------|-----------|------|
| **Project** | id, name, description | has many Repositories, AnalysisRuns |
| **Repository** | id, project_id, provider, remote_url, branches | has many SourceFiles, Findings, CommitSignals |
| **AnalysisRun** | id, project_id, repository_ids, status, progress, logs | has many Findings, Metrics, Feedbacks, Recommendations, Exports |
| **SourceFile** | id, repository_id, path, language, size, hash, owner_hint | has many CodeSymbols |
| **CodeSymbol** | id, file_id, kind, name, location, signature, complexity | belongs to SourceFile |
| **Finding** | id, run_id, repository_id, file_id, tool, rule_id, severity, category, fingerprint | belongs to AnalysisRun, Repository |
| **MetricSnapshot** | id, run_id, scope_type, scope_id, metric_name, value | belongs to AnalysisRun |
| **CommitSignal** | id, repository_id, file_id, commit_sha, author, purpose_category | belongs to Repository |
| **Feedback** | id, run_id, rating (1-5), comment, sentiment_score | belongs to AnalysisRun |
| **Recommendation** | id, run_id, target_type, priority_score, rationale, contributing_signals | belongs to AnalysisRun |
| **ExportReport** | id, run_id, title, format, content | belongs to AnalysisRun |

### 상태 전이

```
queued → running → completed
                  → failed
                  → cancelled
```

---

## Scoring System

### 우선순위 점수 계산

```
priority_score = (
    finding_score     × 0.35 +
    complexity_score  × 0.20 +
    duplication_score × 0.10 +
    dependency_score  × 0.10 +
    change_freq_score × 0.15 +
    feedback_score    × 0.10
) × 10
```

### 피드백 점수 계산

```
improvement_score = star_rating × 0.7 + sentiment_score × 0.3
```

- `star_rating`: 사용자 별점 (1~5)
- `sentiment_score`: 키워드 기반 감성 점수 (1.0~5.0)
  - 긍정/부정 키워드 비율에 따라 계산
  - 키워드 없으면 중립 (3.0)

### 피드백 제출 시 추천 점수 재계산

```
new_feedback_score = (old_feedback_score + improvement_score) / 2
```

---

## Testing

```bash
# 전체 테스트 실행 (55 tests)
python -m unittest discover tests -v

# 특정 테스트 클래스만 실행
python -m unittest tests.test_core.TestModels -v
python -m unittest tests.test_core.TestAPI -v
python -m unittest tests.test_core.TestCommitClassifier -v

# 특정 테스트만 실행
python -m unittest tests.test_core.TestRetryPreservation.test_retry_preserves_other_repo_findings -v
```

### 테스트 커버리지

| 영역 | 테스트 수 | 설명 |
|------|:--------:|------|
| Models | 6 | CRUD, 관계, 라이프사이클 |
| API | 5 | 프로젝트, 저장소, 피드백, 익스포트, 밸리데이션 |
| AST Engine | 4 | Python/JS AST 파싱, 복잡도, import 추출 |
| Complexity | 2 | Python 복잡도, Generic 복잡도 |
| Duplication | 2 | 중복 탐지, 중복 없음 케이스 |
| Dependencies | 1 | 내부/외부 의존성 분석 |
| Commit Classifier | 9 | 규칙 기반 분류, 배치 분류, 클러스터링, 지도 전환 |
| Change Frequency | 1 | 파일/작성자 변경 빈도 |
| Scoring | 2 | finding 점수, 우선순위 점수 |
| Sentiment | 5 | 긍정/부정/중립/한국어/개선 점수 |
| Fixture Files | 10 | 4개 언어 × AST + 복잡도 + 중복 + import |
| Frontend Pages | 6 | 모든 페이지 렌더링 확인 |
| Retry Preservation | 2 | 선택적 재시도, 피드백 재계산 |

---

## Production Deployment

### Gunicorn (Linux/macOS)

```bash
pip install gunicorn

# 4 worker로 실행
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app\()

# 백그라운드 실행
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app\(\) --daemon
```

### Windows (Waitress)

```bash
pip install waitress

# waitress 실행
python -c "from waitress import serve; from app import create_app; serve(create_app(), host='0.0.0.0', port=5000)"
```

### 보안 권장사항

1. **SECRET_KEY 설정**: `export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")`
2. **방화벽**: `data/repos/` 디렉토리에 외부 접근 차단
3. **토큰**: `GITHUB_TOKEN`, `GITLAB_TOKEN`을 환경변수로만 주입 (코드에 하드코딩 금지)
4. **리버스 프록시**: Nginx 뒤에서 실행하여 HTTPS, rate limiting 적용

```nginx
server {
    listen 443 ssl;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### `git clone` 실패

```
# GitHub 인증 오류
→ GITHUB_TOKEN 환경변수 설정 확인
→ Personal Access Token에 repo 스코프가 있는지 확인

# 로컬 경로 접근 불가
→ provider를 "local"로 설정하고 절대경로 사용
→ Windows: C:\Projects\my-repo  (역슬래시)
→ Linux/macOS: /home/user/my-repo
```

### 분석기 도구를 찾을 수 없음

```
# 각 도구가 PATH에 있는지 확인
cppcheck --version
pylint --version
bandit --version
pmd --version
eslint --version

# 없으면 대시보드는 내장 AST 분석만 수행
→ 로그에 "No <language> static analyzers available" 메시지 출력
```

### 데이터베이스 초기화 오류

```bash
# SQLite DB 재생성
rm data/dashboard.db   # macOS/Linux
del data\dashboard.db  # Windows
python app.py           # 재시작 시 자동 생성
```

### 분석이 너무 오래 걸림

```
→ MAX_ANALYSIS_TIMEOUT 환경변수로 제한 시간 설정
→ 분석 기간을 1주(1w)로 줄이기
→ 대용량 저장소는 브랜치 필터 사용
→ 로그에서 "WARNING: Truncating analysis to 200 files" 메시지 확인
```

### 포트 충돌

```bash
# 다른 포트로 실행 (Linux/macOS)
FLASK_RUN_PORT=8080 python app.py

# Windows PowerShell
$env:FLASK_RUN_PORT = "8080"
python app.py
```

---

## Export Guide

| Format | 대상 | 용도 |
|--------|------|------|
| **Markdown** (.md) | AI 코딩 에이전트 | Findings, Recommendations, Feedback 포함 핸드오프 문서 |
| **JSON** (.json) | 자동화 도구 | CI/CD 파이프라인, 알림 시스템 연동 |
| **Dashboard HTML** | 개발자, 팀장 | 인터랙티브 차트, 필터, 드릴다운으로 직접 탐색 |

---

## License

이 프로젝트는 오픈소스 도구를 사용합니다. 통합된 외부 도구의 라이선스를 배포 전에 검토하세요:

- cppcheck: GPL v3
- pylint: GPL v2
- bandit: Apache 2.0
- PMD: BSD-style
- ESLint: MIT
