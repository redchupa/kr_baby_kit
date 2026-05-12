"""Constants for 한국 영유아 키트 (Korean Baby Kit)."""
from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

DOMAIN = "kr_baby_kit"
LOGGER = logging.getLogger(__package__)
TZ_ASIA_SEOUL = ZoneInfo("Asia/Seoul")

# Config entry keys
CONF_CHILD_NAME = "child_name"
CONF_CHILD_BIRTHDATE = "child_birthdate"
CONF_CHILD_SEX = "child_sex"
CONF_CHILD_ID = "child_id"

SEX_MALE = "male"
SEX_FEMALE = "female"
SEX_OPTIONS = [SEX_MALE, SEX_FEMALE]

# Measurement record storage
STORAGE_KEY_RECORDS = "kr_baby_kit_records"
STORAGE_VERSION = 1

MEASUREMENT_HEIGHT = "height"
MEASUREMENT_WEIGHT = "weight"
MEASUREMENT_HEAD = "head"
MEASUREMENT_BMI = "bmi"
MEASUREMENT_KINDS = [
    MEASUREMENT_HEIGHT,
    MEASUREMENT_WEIGHT,
    MEASUREMENT_HEAD,
    MEASUREMENT_BMI,
]

# Donation meta — intentionally surfaced on every device entry.
# Original family/household identifiers must NOT appear anywhere else.
DONATION_MANUFACTURER = "우*만"
DONATION_MODEL = "토스 1000-1261-7813"
DONATION_SW_VERSION = "커피 한잔은 사랑입니다 ☕"

# Attribution string surfaced on entities/devices per 공공누리 제1유형
ATTRIBUTION = "질병관리청 2017 소아청소년 성장도표 · 표준 예방접종 일정"

# Disclaimer — referenced by services, LLM tool, and dashboards
MEDICAL_DISCLAIMER = (
    "본 정보는 참고용이며 의료기관 진료를 대체하지 않습니다."
)
