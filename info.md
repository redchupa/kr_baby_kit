# 한국 영유아 키트 (Korean Baby Kit)

Home Assistant 통합 — 한국 영유아 데이터를 HA로.

- 📏 **성장곡선** — 질병관리청 2017 소아청소년 성장도표 (LMS) 기반 키/몸무게/머리둘레/BMI/신장별 체중 백분위
- 💉 **예방접종** — 표준 NIP 일정으로 다가오는 접종 자동 캘린더화
- 🩺 **영유아 검진** — 보건복지부 표준 8회 검진 일정 캘린더 (생후 14~35일 초기 검진 포함)
- 🦷 **영유아 구강검진** — 국민건강보험공단 4회 (18~29 · 30~41 · 42~53 · 54~65개월) 센서·캘린더
- ✅ **완료 표시** — 접종·검진을 완료로 표시하면 다음 일정에서 자동 제외, 캘린더에 ✅/⚠️ 표시
- ✍️ **간편 입력** — 대시보드의 number 슬라이더로 측정값 즉시 기록
- 🎙️ **Assist 연동** — "다음 접종 언제?", "키 백분위 알려줘" 자연어 쿼리

모든 데이터는 공공 데이터(공공누리 제1유형). 외부 API 키 없이 오프라인 동작.

> ⚠️ 본 정보는 참고용이며 의료기관 진료를 대체하지 않습니다.

## 영문 요약

Home Assistant integration exposing Korean infant/child reference data
(KDCA 2017 growth charts, NIP immunization schedule, 보건복지부 8-stage
health checkups). Includes a `number` platform for one-tap measurement
entry from the dashboard and an LLM API for voice queries. Bundled
public-data tables only — no API keys required.

후원: 토스 1000-1261-7813 (우*만) ☕
