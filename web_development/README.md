# ThermoGuard - 열화상 공장 안전 모니터링

로봇 자동화 공장의 열화상 카메라 온도를 모니터링하고 과열·화재 위험을 알리는 학습용 웹 프로젝트입니다. 현재는 실제 카메라 대신 서버가 생성하는 가짜 온도와 브라우저가 그리는 열화상 화면을 사용합니다.

## 구현된 기능

- 관리자와 일반 회원 로그인 및 권한 분리
- 공장 전체 상태, 최고·평균 온도, 온도 그래프 대시보드
- 로봇팔·모터용 단일 열화상 카메라 실시간 모니터링
- 베이스·어깨·손목 모터의 과열 지점과 개별 온도 오버레이
- 카메라 상세 열화상 화면과 온도 이력
- 60°C 이상 주의, 80°C 이상 위험 판정 및 경고 기록
- 관리자의 경고 확인 처리
- 관리자의 임계온도 변경
- 관리자의 사용자 추가·활성화·비활성화
- PC, 태블릿, 모바일 반응형 화면
- SQLite 데이터베이스 자동 생성

## 초보자를 위한 구조 설명

```text
web_development/
├─ app.py                 Flask 서버, 화면 주소, API, DB 처리
├─ requirements.txt       설치할 Python 패키지 목록
├─ instance/
│  └─ monitoring.db       첫 실행 시 자동 생성되는 SQLite DB
├─ templates/             브라우저에 전달할 HTML 화면
│  ├─ base.html           로그인 이후 화면의 공통 메뉴
│  ├─ login.html          로그인
│  ├─ dashboard.html      메인 대시보드
│  ├─ cameras.html        카메라 목록
│  ├─ camera_detail.html  카메라 상세
│  ├─ alerts.html         경고 내역
│  ├─ settings.html       임계온도 설정
│  └─ users.html          사용자 관리
├─ static/
│  ├─ css/style.css       색상, 배치, 모바일 디자인
│  └─ js/app.js           API 호출, 그래프, 열화상 화면
└─ tests/test_app.py      로그인·권한·API 자동 테스트
```

브라우저는 `app.js`에서 4초마다 `/api/snapshot`을 호출합니다. Flask는 새로운 가상 온도를 계산해 SQLite에 저장한 뒤 JSON으로 돌려줍니다. JavaScript는 받은 데이터로 숫자, 상태, 그래프와 이미지 위 모터별 과열 위치를 다시 표시합니다.

## 1. Python 설치

Python 3.11 이상을 설치합니다. Windows 설치 화면에서 **Add python.exe to PATH**를 체크하세요.

설치 확인:

```powershell
python --version
```

## 2. 가상환경과 패키지 설치

PowerShell에서 이 폴더로 이동한 다음 실행합니다.

```powershell
cd web_development
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

PowerShell이 스크립트 실행을 차단하면 현재 터미널에서만 다음 명령을 먼저 실행합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. 서버 실행

```powershell
python app.py
```

브라우저에서 <http://127.0.0.1:5000>을 엽니다.

### 테스트 계정

| 권한 | 아이디 | 비밀번호 |
|---|---|---|
| 관리자 | `admin` | `admin1234` |
| 일반 회원 | `member` | `member1234` |

관리자는 설정과 사용자 관리 메뉴가 보이고, 일반 회원에게는 이 메뉴가 보이지 않습니다.

## 4. 자동 테스트

서버를 종료한 상태에서 실행합니다.

```powershell
python -m unittest discover -s tests -v
```

## 데이터베이스 초기화

학습 중 데이터를 처음 상태로 되돌리고 싶다면 서버를 종료하고 `instance/monitoring.db`만 삭제한 뒤 다시 실행합니다. 테이블, 테스트 계정, 카메라와 샘플 데이터가 자동으로 만들어집니다.

## 실제 열화상 카메라 연결 위치

현재 가짜 데이터는 `app.py`의 `simulate_if_due()` 함수에서 생성합니다. 실제 장비를 연결할 때는 이 함수를 카메라 제조사가 제공하는 HTTP API, SDK 또는 스트림 수신 코드로 교체합니다. 프론트엔드가 사용하는 JSON 필드는 아래처럼 유지하면 화면 코드는 대부분 변경하지 않아도 됩니다.

```json
{
  "camera_id": "CAM-01",
  "location": "로봇 조립 1구역",
  "max_temperature": 72.5,
  "average_temperature": 44.2,
  "current_temperature": 48.1,
  "status": "warning",
  "captured_at": "2026-07-13T14:30:00"
}
```

## 실제 운영 전 보완할 점

이 프로젝트는 학습·시연용입니다. 공장에 실제 배포하기 전에는 다음 작업이 필요합니다.

- 환경 변수로 강력한 `SECRET_KEY` 설정
- HTTPS 적용과 사내 인증 체계 연동
- 실제 카메라 연결 오류 및 재접속 처리
- 이메일, 문자 또는 사내 메신저 경고 발송
- 경고 기록 백업과 감사 로그
- 운영용 WSGI 서버와 리버스 프록시 적용
- 현장 기준에 맞춘 임계온도 검증

실제 화재 경보 장치를 이 웹만으로 대체하면 안 됩니다. 인증된 화재 감지·경보 설비를 함께 사용해야 합니다.
