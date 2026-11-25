/* Home Assistant Sidebar Panel for Baby Kit (kr_baby_kit) */
import { THEMES, getThemeCss } from "./themes.js?v=0.13.0";

const PREFS_KEY = "kr_baby_kit_panel_prefs_v2";

const DEFAULT_PREFS = {
  theme: "ha-native",
  layout: "single", // "single" | "bento" | "compact"
  order: ["care", "timeline", "measurements", "growth", "tuition", "schedules"],
  visible: {
    care: true,
    timeline: true,
    measurements: true,
    growth: true,
    tuition: true,
    schedules: true,
    footer: true,
  },
  defaultScheduleTab: "vaccines",
};

const STRINGS = {
  ko: {
    title: "Baby Kit",
    addChild: "아이 추가",
    editChild: "정보 수정",
    deleteChild: "삭제",
    deleteConfirm: "이 아이와 저장된 측정 기록·돌봄 기록·사진을 모두 삭제할까요?",
    noChildren: "등록된 아이가 없습니다. 위 버튼으로 아이를 추가하세요.",
    name: "이름 또는 별칭",
    namePlaceholder: "예: 첫째, 둘째",
    birthdate: "생년월일",
    sex: "성별",
    male: "남아",
    female: "여아",
    profile: "지역 / 기준",
    profileKr: "대한민국 (질병관리청 · NIP · 보육료)",
    profileGlobal: "해외 (WHO 성장 표준)",
    save: "저장",
    cancel: "취소",
    close: "닫기",
    saving: "저장 중...",
    saved: "저장되었습니다.",
    changePhoto: "프로필 사진 변경",
    ageMonths: (m) => `생후 ${m}개월`,
    careTitle: "오늘의 돌봄 · 타이머",
    todaySleep: "수면",
    todayFeed: "수유",
    todayDiaper: "기저귀",
    todayTummy: "터미타임",
    todayTemp: "최근 체온",
    minUnit: "분",
    countUnit: "회",
    wet: "소변",
    solid: "대변",
    both: "소변+대변",
    timerStart: "시작",
    timerStop: "종료·저장",
    timerCancel: "취소",
    kindNote: "메모·사진",
    kindFeeding: "수유",
    kindSleep: "수면",
    kindDiaper: "기저귀",
    kindTummy: "터미타임",
    kindPumping: "유축",
    kindTemp: "체온",
    methodLabel: "방법",
    methodBreastL: "모유 (좌)",
    methodBreastR: "모유 (우)",
    methodBreastB: "모유 (양쪽)",
    methodBottle: "젖병 (모유)",
    methodFormula: "분유",
    methodSolid: "이유식",
    amountMl: "양 (ml)",
    durationMin: "시간 (분)",
    diaperType: "종류",
    tempC: "체온 (°C)",
    noteLabel: "메모",
    notePlaceholder: "오늘 있었던 일, 특이사항, 발달 기록...",
    attachPhoto: "사진 첨부",
    removePhoto: "사진 제거",
    logSave: "기록 저장",
    timelineTitle: "타임라인 · 사진 일기",
    filterAll: "전체",
    filterPhotos: "사진만",
    noActivities: "아직 기록이 없습니다. 위에서 수유·수면·기저귀 또는 사진 일기를 남겨보세요.",
    measurements: "성장 측정 입력",
    height: "키 (cm)",
    weight: "몸무게 (kg)",
    head: "머리둘레 (cm)",
    measureDate: "측정일",
    saveMeasurement: "측정값 저장",
    defaultMedian: "평균 기본값",
    recordedAt: (d) => `최근 기록: ${d}`,
    growthSummary: "성장 백분위",
    noMeasureYet: "아직 측정 기록이 없습니다. 위에서 키·몸무게·머리둘레를 저장하면 백분위가 계산됩니다.",
    bmi: "BMI",
    concernOk: "정상 범위",
    concernWarn: "주의 필요",
    concernHead: "머리둘레",
    concernBmi: "BMI",
    concernWfl: "신장별 몸무게",
    under24Note: "만 24개월 미만은 신장별 몸무게를 참고합니다.",
    schedules: "일정 관리",
    tabVaccines: "예방접종",
    tabCheckups: "건강검진",
    tabOral: "구강검진",
    statusOpen: "지금 가능",
    statusUpcoming: "예정",
    statusDone: "완료",
    statusPast: "기간 지남",
    markDone: "완료 표시",
    unmarkDone: "완료 취소",
    showPast: "지난 일정 보기",
    tuition: "어린이집 보육료",
    tuitionStd: "월 표준보육료",
    tuitionSub: "월 정부지원금",
    tuitionShare: "월 본인부담금",
    won: "원",
    modalAddTitle: "아이 추가",
    modalEditTitle: "아이 정보 수정",
    settingsTitle: "화면 및 테마 설정",
    settingsTheme: "테마 선택 (12종)",
    settingsLayout: "레이아웃 구성",
    layoutSingle: "1열 표준",
    layoutBento: "2열 대시보드",
    layoutCompact: "컴팩트",
    settingsSections: "섹션 표시 및 순서",
    secCare: "오늘의 돌봄 · 타이머",
    secTimeline: "타임라인 · 사진 일기",
    secMeasurements: "성장 측정 입력",
    secGrowth: "성장 백분위",
    secTuition: "어린이집 보육료 (KR)",
    secSchedules: "일정 관리",
    secFooter: "하단 면책·출처 표시",
    settingsDefaultTab: "기본 일정 탭",
    resetPrefs: "기본값으로 초기화",
  },
  en: {
    title: "Baby Kit",
    addChild: "Add child",
    editChild: "Edit info",
    deleteChild: "Delete",
    deleteConfirm: "Delete this child along with all measurements, care logs, and photos?",
    noChildren: "No children registered yet. Use the button above to add a child.",
    name: "Name or alias",
    namePlaceholder: "e.g. Baby A",
    birthdate: "Birthdate",
    sex: "Sex",
    male: "Male",
    female: "Female",
    profile: "Region / Standard",
    profileKr: "South Korea (KDCA, NIP, Childcare Tuition)",
    profileGlobal: "International (WHO Growth Standards)",
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    saving: "Saving...",
    saved: "Saved.",
    changePhoto: "Change profile photo",
    ageMonths: (m) => `${m} mo`,
    careTitle: "Daily Care & Timers",
    todaySleep: "Sleep",
    todayFeed: "Feeding",
    todayDiaper: "Diapers",
    todayTummy: "Tummy time",
    todayTemp: "Last temp",
    minUnit: "m",
    countUnit: "x",
    wet: "Wet",
    solid: "Solid",
    both: "Wet + Solid",
    timerStart: "Start",
    timerStop: "Stop & save",
    timerCancel: "Cancel",
    kindNote: "Note & Photo",
    kindFeeding: "Feeding",
    kindSleep: "Sleep",
    kindDiaper: "Diaper",
    kindTummy: "Tummy time",
    kindPumping: "Pumping",
    kindTemp: "Temp",
    methodLabel: "Method",
    methodBreastL: "Breast (L)",
    methodBreastR: "Breast (R)",
    methodBreastB: "Breast (Both)",
    methodBottle: "Bottle (milk)",
    methodFormula: "Formula",
    methodSolid: "Solid food",
    amountMl: "Amount (ml)",
    durationMin: "Duration (min)",
    diaperType: "Type",
    tempC: "Temp (°C)",
    noteLabel: "Note",
    notePlaceholder: "Milestones, symptoms, daily memories...",
    attachPhoto: "Attach photo",
    removePhoto: "Remove photo",
    logSave: "Save entry",
    timelineTitle: "Timeline & Photo Diary",
    filterAll: "All",
    filterPhotos: "Photos",
    noActivities: "No care logs yet. Record a feeding, sleep, diaper change, or photo note above.",
    measurements: "Growth measurements",
    height: "Height (cm)",
    weight: "Weight (kg)",
    head: "Head circumference (cm)",
    measureDate: "Date",
    saveMeasurement: "Save measurement",
    defaultMedian: "Age median",
    recordedAt: (d) => `Last recorded: ${d}`,
    growthSummary: "Growth percentiles",
    noMeasureYet: "No measurements recorded yet. Save height, weight, or head circumference above to compute percentiles.",
    bmi: "BMI",
    concernOk: "Normal range",
    concernWarn: "Needs attention",
    concernHead: "Head circumference",
    concernBmi: "BMI",
    concernWfl: "Weight-for-length",
    under24Note: "Under 24 months: check weight-for-length instead of BMI percentile.",
    schedules: "Schedules",
    tabVaccines: "Immunizations",
    tabCheckups: "Health checkups",
    tabOral: "Dental checkups",
    statusOpen: "Open now",
    statusUpcoming: "Upcoming",
    statusDone: "Done",
    statusPast: "Passed",
    markDone: "Mark done",
    unmarkDone: "Undo",
    showPast: "Show past windows",
    tuition: "Childcare tuition (KR)",
    tuitionStd: "Standard tuition",
    tuitionSub: "Government subsidy",
    tuitionShare: "Parent share",
    won: "KRW",
    modalAddTitle: "Add child",
    modalEditTitle: "Edit child",
    settingsTitle: "Appearance & Layout",
    settingsTheme: "Theme (12 styles)",
    settingsLayout: "Layout mode",
    layoutSingle: "Single column",
    layoutBento: "2-column bento",
    layoutCompact: "Compact",
    settingsSections: "Sections & order",
    secCare: "Daily Care & Timers",
    secTimeline: "Timeline & Photo Diary",
    secMeasurements: "Growth measurements",
    secGrowth: "Growth percentiles",
    secTuition: "Childcare tuition (KR)",
    secSchedules: "Schedules",
    secFooter: "Footer disclaimer & attribution",
    settingsDefaultTab: "Default schedule tab",
    resetPrefs: "Reset to defaults",
  },
};

const GEAR_SVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`;
const CAM_SVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>`;

function esc(val) {
  return String(val ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtElapsed(startedIso) {
  const start = Date.parse(startedIso);
  if (Number.isNaN(start)) return "00:00:00";
  const sec = Math.max(0, Math.floor((Date.now() - start) / 1000));
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function fmtMinutes(min, ko) {
  const total = Math.round(Number(min || 0));
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h > 0) return ko ? `${h}시간 ${m}분` : `${h}h ${m}m`;
  return ko ? `${m}분` : `${m}m`;
}

function fmtTimestamp(iso) {
  if (!iso) return "";
  return String(iso).replace("T", " ").slice(0, 16);
}

function compressImage(file, maxEdge = 1280, quality = 0.82) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Failed to read image file."));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("Invalid image file."));
      img.onload = () => {
        const scale = Math.min(1, maxEdge / Math.max(img.width, img.height));
        const w = Math.max(1, Math.round(img.width * scale));
        const h = Math.max(1, Math.round(img.height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, w, h);
        resolve(canvas.toDataURL("image/jpeg", quality));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

function loadPrefs() {
  try {
    const raw = window.localStorage.getItem(PREFS_KEY);
    if (!raw) return structuredClone(DEFAULT_PREFS);
    const parsed = JSON.parse(raw);
    const validOrder = Array.isArray(parsed.order)
      ? parsed.order.filter((k) => DEFAULT_PREFS.order.includes(k))
      : [];
    for (const k of DEFAULT_PREFS.order) {
      if (!validOrder.includes(k)) validOrder.push(k);
    }
    return {
      theme: THEMES.some((t) => t.id === parsed.theme) ? parsed.theme : DEFAULT_PREFS.theme,
      layout: ["single", "bento", "compact"].includes(parsed.layout) ? parsed.layout : DEFAULT_PREFS.layout,
      order: validOrder,
      visible: { ...DEFAULT_PREFS.visible, ...(parsed.visible || {}) },
      defaultScheduleTab: ["vaccines", "checkups", "oral"].includes(parsed.defaultScheduleTab)
        ? parsed.defaultScheduleTab
        : DEFAULT_PREFS.defaultScheduleTab,
    };
  } catch {
    return structuredClone(DEFAULT_PREFS);
  }
}

function savePrefs(prefs) {
  try {
    window.localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch {
    // Ignore storage quota errors.
  }
}

class KrBabyKitPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._data = null;
    this._selectedId = null;
    this._prefs = loadPrefs();
    this._scheduleTab = this._prefs.defaultScheduleTab;
    this._careKind = "note";
    this._timelineFilter = "all";
    this._pendingPhoto = null;
    this._lightboxUrl = null;
    this._showPast = false;
    this._modal = null;
    this._settingsOpen = false;
    this._busy = false;
    this._notice = null;
    this._error = null;
    this._tickHandle = null;
  }

  connectedCallback() {
    if (!this._tickHandle) {
      this._tickHandle = window.setInterval(() => this._tickTimers(), 1000);
    }
  }

  disconnectedCallback() {
    if (this._tickHandle) {
      window.clearInterval(this._tickHandle);
      this._tickHandle = null;
    }
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._load();
    }
  }

  set narrow(val) {
    this._narrow = Boolean(val);
    this._render();
  }

  _isKo() {
    const lang = (this._hass?.language || this._data?.language || "ko").toLowerCase();
    return lang.startsWith("ko");
  }

  _t() {
    return this._isKo() ? STRINGS.ko : STRINGS.en;
  }

  _tickTimers() {
    const child = this._currentChild();
    if (!child || !this.shadowRoot) return;
    const timers = child.timers || {};
    this.shadowRoot.querySelectorAll("[data-timer-clock]").forEach((el) => {
      const k = el.getAttribute("data-timer-clock");
      if (timers[k]?.started_at) {
        el.textContent = fmtElapsed(timers[k].started_at);
      }
    });
  }

  _updatePrefs(mutator) {
    const next = structuredClone(this._prefs);
    mutator(next);
    this._prefs = next;
    savePrefs(next);
    this._render();
  }

  async _load() {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({ type: "kr_baby_kit/get_overview" });
      this._data = res;
      const children = res.children || [];
      if (!children.some((c) => c.entry_id === this._selectedId)) {
        this._selectedId = children[0]?.entry_id || null;
      }
      this._error = null;
    } catch (err) {
      this._error = err?.message || String(err);
    }
    this._render();
  }

  _currentChild() {
    const children = this._data?.children || [];
    return children.find((c) => c.entry_id === this._selectedId) || children[0] || null;
  }

  _flash(msg) {
    this._notice = msg;
    this._render();
    setTimeout(() => {
      if (this._notice === msg) {
        this._notice = null;
        this._render();
      }
    }, 2500);
  }

  async _uploadAvatar(file) {
    const child = this._currentChild();
    if (!child || !file || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      const dataUrl = await compressImage(file, 512, 0.85);
      await this._hass.callWS({
        type: "kr_baby_kit/set_avatar",
        child_id: child.child_id,
        photo_data_url: dataUrl,
      });
      await this._load();
      this._flash(this._t().saved);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _startTimer(kind) {
    const child = this._currentChild();
    if (!child || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS({
        type: "kr_baby_kit/start_timer",
        child_id: child.child_id,
        kind,
      });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _stopTimer(kind, saveLog) {
    const child = this._currentChild();
    if (!child || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS({
        type: "kr_baby_kit/stop_timer",
        child_id: child.child_id,
        kind,
        save_log: saveLog,
      });
      await this._load();
      if (saveLog) this._flash(this._t().saved);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _saveActivity(ev) {
    ev.preventDefault();
    const child = this._currentChild();
    if (!child || this._busy) return;
    const form = ev.target;
    const payload = {
      type: "kr_baby_kit/add_activity",
      child_id: child.child_id,
      kind: this._careKind,
    };
    const numField = (name) => {
      const raw = form.querySelector(`[name='${name}']`)?.value?.trim();
      return raw !== "" && raw != null ? Number(raw) : null;
    };
    const strField = (name) => form.querySelector(`[name='${name}']`)?.value?.trim() || "";

    const dur = numField("duration_min");
    if (dur != null) payload.duration_min = dur;
    const ml = numField("amount_ml");
    if (ml != null) payload.amount_ml = ml;
    const method = strField("method");
    if (method) payload.method = method;
    const diaper = strField("diaper_type");
    if (diaper) payload.diaper_type = diaper;
    const temp = numField("temperature_c");
    if (temp != null) payload.temperature_c = temp;
    const note = strField("note");
    if (note) payload.note = note;
    if (this._pendingPhoto) payload.photo_data_url = this._pendingPhoto;

    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS(payload);
      this._pendingPhoto = null;
      await this._load();
      this._flash(this._t().saved);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _deleteActivity(activityId) {
    const child = this._currentChild();
    if (!child || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS({
        type: "kr_baby_kit/delete_activity",
        child_id: child.child_id,
        activity_id: activityId,
      });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _saveMeasurement(ev) {
    ev.preventDefault();
    const child = this._currentChild();
    if (!child || this._busy) return;
    const form = ev.target;
    const payload = { child_id: child.child_id };
    const dateVal = form.querySelector("[name='date']")?.value?.trim();
    if (dateVal) payload.date = dateVal;
    for (const k of ["height", "weight", "head"]) {
      const raw = form.querySelector(`[name='${k}']`)?.value?.trim();
      if (raw !== "" && raw != null) payload[k] = Number(raw);
    }
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callService("kr_baby_kit", "record_measurement", payload);
      await this._load();
      this._flash(this._t().saved);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _toggleDone(eventId, isDone) {
    const child = this._currentChild();
    if (!child || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      const svc = isDone ? "unmark_event_done" : "mark_event_done";
      await this._hass.callService("kr_baby_kit", svc, {
        child_id: child.child_id,
        event_id: eventId,
      });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _submitModal(ev) {
    ev.preventDefault();
    if (!this._modal || this._busy) return;
    const form = ev.target;
    const child_name = form.querySelector("[name='child_name']")?.value?.trim() || "";
    const child_birthdate = form.querySelector("[name='child_birthdate']")?.value?.trim() || "";
    const child_sex = form.querySelector("[name='child_sex']")?.value || "male";
    const profile = form.querySelector("[name='profile']")?.value || "kr";

    this._busy = true;
    this._error = null;
    this._render();
    try {
      if (this._modal.mode === "add") {
        const res = await this._hass.callWS({
          type: "kr_baby_kit/add_child",
          child_name,
          child_birthdate,
          child_sex,
          profile,
        });
        this._modal = null;
        if (res?.entry_id) this._selectedId = res.entry_id;
      } else {
        await this._hass.callWS({
          type: "kr_baby_kit/update_child",
          entry_id: this._modal.child.entry_id,
          child_name,
          child_birthdate,
          child_sex,
          profile,
        });
        this._modal = null;
      }
      await this._load();
      this._flash(this._t().saved);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _deleteChild() {
    if (!this._modal?.child || this._busy) return;
    if (!window.confirm(this._t().deleteConfirm)) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS({
        type: "kr_baby_kit/delete_child",
        entry_id: this._modal.child.entry_id,
      });
      this._modal = null;
      this._selectedId = null;
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  _openSidebar() {
    this.dispatchEvent(
      new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true })
    );
  }

  _kindLabel(kind) {
    const t = this._t();
    const map = {
      note: t.kindNote,
      feeding: t.kindFeeding,
      sleep: t.kindSleep,
      diaper: t.kindDiaper,
      tummy_time: t.kindTummy,
      pumping: t.kindPumping,
      temperature: t.kindTemp,
    };
    return map[kind] || kind;
  }

  _methodLabel(m) {
    const t = this._t();
    const map = {
      breast_left: t.methodBreastL,
      breast_right: t.methodBreastR,
      breast_both: t.methodBreastB,
      bottle: t.methodBottle,
      formula: t.methodFormula,
      solid: t.methodSolid,
    };
    return map[m] || m;
  }

  _diaperLabel(d) {
    const t = this._t();
    if (d === "wet") return t.wet;
    if (d === "solid") return t.solid;
    if (d === "both") return t.both;
    return d;
  }

  _renderConcernBadge(label, pct, summary) {
    const t = this._t();
    if (pct == null) {
      return `
        <div class="concern-row">
          <span class="concern-label">${esc(label)}</span>
          <span class="muted">${esc(summary || "-")}</span>
        </div>`;
    }
    const warn = pct < 5 || pct > 95;
    return `
      <div class="concern-row">
        <span class="concern-label">${esc(label)}</span>
        <span class="badge ${warn ? "warn" : "ok"}">${esc(warn ? t.concernWarn : t.concernOk)}</span>
        <span class="muted">${esc(summary || "")}</span>
      </div>`;
  }

  _renderScheduleList(child) {
    const t = this._t();
    const ko = this._isKo();
    const list =
      this._scheduleTab === "vaccines"
        ? child.vaccines || []
        : this._scheduleTab === "checkups"
        ? child.checkups || []
        : child.oral_checkups || [];

    const filtered = this._showPast
      ? list
      : list.filter((e) => e.status === "open" || e.status === "upcoming" || e.status === "done");

    if (!filtered.length) {
      return `<p class="muted">-</p>`;
    }
    return filtered
      .slice(0, 25)
      .map((e) => {
        const name = ko ? e.name_ko : e.name_en || e.name_ko;
        const dose = e.kind === "vaccine" && e.dose ? (ko ? ` ${e.dose}차` : ` #${e.dose}`) : "";
        const statusLabel =
          e.status === "open"
            ? t.statusOpen
            : e.status === "upcoming"
            ? t.statusUpcoming
            : e.status === "done"
            ? t.statusDone
            : t.statusPast;
        const isDone = e.status === "done";
        const btnText = isDone ? t.unmarkDone : t.markDone;
        return `
          <div class="sched-item">
            <div class="sched-main">
              <div class="sched-title">
                <span class="badge status-${esc(e.status)}">${esc(statusLabel)}</span>
                <strong>${esc(name + dose)}</strong>
              </div>
              <div class="muted small">${esc(e.window_start)} ~ ${esc(e.window_end)}${e.completed_date ? ` (${esc(e.completed_date)})` : ""}</div>
            </div>
            <button class="btn-outline small" data-toggle-done="${esc(e.event_id)}" data-is-done="${isDone ? "1" : "0"}" ${this._busy ? "disabled" : ""}>${esc(btnText)}</button>
          </div>`;
      })
      .join("");
  }

  _renderCareFormFields() {
    const t = this._t();
    const k = this._careKind;
    if (k === "feeding") {
      return `
        <div class="grid-3">
          <label>${esc(t.methodLabel)}
            <select name="method">
              <option value="formula">${esc(t.methodFormula)}</option>
              <option value="bottle">${esc(t.methodBottle)}</option>
              <option value="breast_left">${esc(t.methodBreastL)}</option>
              <option value="breast_right">${esc(t.methodBreastR)}</option>
              <option value="breast_both">${esc(t.methodBreastB)}</option>
              <option value="solid">${esc(t.methodSolid)}</option>
            </select>
          </label>
          <label>${esc(t.amountMl)}
            <input name="amount_ml" type="number" step="5" min="0" max="1000" placeholder="140" />
          </label>
          <label>${esc(t.durationMin)}
            <input name="duration_min" type="number" step="1" min="0" max="300" placeholder="15" />
          </label>
        </div>`;
    }
    if (k === "sleep" || k === "tummy_time") {
      return `
        <div class="grid-3">
          <label>${esc(t.durationMin)}
            <input name="duration_min" type="number" step="1" min="1" max="1440" placeholder="${k === "sleep" ? "90" : "15"}" />
          </label>
        </div>`;
    }
    if (k === "diaper") {
      return `
        <div class="grid-3">
          <label>${esc(t.diaperType)}
            <select name="diaper_type">
              <option value="wet">${esc(t.wet)}</option>
              <option value="solid">${esc(t.solid)}</option>
              <option value="both">${esc(t.both)}</option>
            </select>
          </label>
        </div>`;
    }
    if (k === "pumping") {
      return `
        <div class="grid-3">
          <label>${esc(t.amountMl)}
            <input name="amount_ml" type="number" step="5" min="0" max="1000" placeholder="120" />
          </label>
          <label>${esc(t.durationMin)}
            <input name="duration_min" type="number" step="1" min="0" max="180" placeholder="20" />
          </label>
        </div>`;
    }
    if (k === "temperature") {
      return `
        <div class="grid-3">
          <label>${esc(t.tempC)}
            <input name="temperature_c" type="number" step="0.1" min="34" max="43" placeholder="36.7" required />
          </label>
        </div>`;
    }
    return "";
  }

  _renderSection(secId, child) {
    const t = this._t();
    const ko = this._isKo();
    if (!this._prefs.visible[secId]) return "";

    if (secId === "care") {
      const sum = child.today_summary || {};
      const timers = child.timers || {};
      const timerKinds = ["sleep", "feeding", "tummy_time", "pumping"];
      const logKinds = ["note", "feeding", "sleep", "diaper", "tummy_time", "pumping", "temperature"];

      const timerCards = timerKinds
        .map((tk) => {
          const active = Boolean(timers[tk]?.started_at);
          return `
            <div class="timer-tile ${active ? "running" : ""}">
              <div class="timer-top">
                <span class="timer-name">${esc(this._kindLabel(tk))}</span>
                <span class="timer-clock" data-timer-clock="${esc(tk)}">${active ? esc(fmtElapsed(timers[tk].started_at)) : "00:00:00"}</span>
              </div>
              <div class="timer-btns">
                ${
                  active
                    ? `<button type="button" class="btn-primary small" data-stop-timer="${esc(tk)}" ${this._busy ? "disabled" : ""}>${esc(t.timerStop)}</button>
                       <button type="button" class="btn-outline small" data-cancel-timer="${esc(tk)}" ${this._busy ? "disabled" : ""}>${esc(t.timerCancel)}</button>`
                    : `<button type="button" class="btn-outline small" data-start-timer="${esc(tk)}" ${this._busy ? "disabled" : ""}>${esc(t.timerStart)}</button>`
                }
              </div>
            </div>`;
        })
        .join("");

      return `
        <div class="card section-card span-full" data-section="care">
          <h3>${esc(t.careTitle)}</h3>
          <div class="summary-strip">
            <div class="stat">
              <div class="muted small">${esc(t.todaySleep)}</div>
              <div class="stat-val">${esc(fmtMinutes(sum.sleep_min, ko))}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.todayFeed)}</div>
              <div class="stat-val">${sum.feeding_count || 0}${esc(t.countUnit)}${sum.feeding_ml ? ` · ${sum.feeding_ml}ml` : ""}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.todayDiaper)}</div>
              <div class="stat-val">${esc(t.wet)} ${sum.diaper_wet || 0} / ${esc(t.solid)} ${sum.diaper_solid || 0}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.todayTummy)}</div>
              <div class="stat-val">${esc(fmtMinutes(sum.tummy_min, ko))}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.todayTemp)}</div>
              <div class="stat-val">${sum.last_temp_c != null ? `${sum.last_temp_c}°C` : "-"}</div>
            </div>
          </div>

          <div class="timer-grid">${timerCards}</div>

          <div class="tabs care-tabs">
            ${logKinds
              .map(
                (lk) =>
                  `<button type="button" class="tab ${this._careKind === lk ? "active" : ""}" data-care-kind="${esc(lk)}">${esc(this._kindLabel(lk))}</button>`
              )
              .join("")}
          </div>

          <form id="care-form" class="care-form">
            ${this._renderCareFormFields()}
            <label>${esc(t.noteLabel)}
              <textarea name="note" rows="2" placeholder="${esc(t.notePlaceholder)}"></textarea>
            </label>
            <div class="photo-row">
              <label class="btn-outline small photo-upload-btn">
                ${CAM_SVG} <span>${esc(t.attachPhoto)}</span>
                <input type="file" id="care-photo-input" accept="image/*" hidden />
              </label>
              ${
                this._pendingPhoto
                  ? `<div class="photo-preview-wrap">
                       <img src="${esc(this._pendingPhoto)}" class="photo-preview" alt="preview" />
                       <button type="button" class="btn-outline small" id="btn-remove-photo">${esc(t.removePhoto)}</button>
                     </div>`
                  : ""
              }
              <button type="submit" class="btn-primary" style="margin-left:auto;" ${this._busy ? "disabled" : ""}>${esc(this._busy ? t.saving : t.logSave)}</button>
            </div>
          </form>
        </div>`;
    }

    if (secId === "timeline") {
      const items = child.activities || [];
      const filters = ["all", "photos", "feeding", "sleep", "diaper", "tummy_time", "temperature", "note"];
      const filtered = items.filter((a) => {
        if (this._timelineFilter === "all") return true;
        if (this._timelineFilter === "photos") return Boolean(a.photo_url);
        return a.kind === this._timelineFilter;
      });

      const listHtml = !filtered.length
        ? `<p class="muted">${esc(t.noActivities)}</p>`
        : filtered
            .slice(0, 40)
            .map((a) => {
              const details = [];
              if (a.method) details.push(this._methodLabel(a.method));
              if (a.amount_ml != null) details.push(`${a.amount_ml} ml`);
              if (a.duration_min != null) details.push(fmtMinutes(a.duration_min, ko));
              if (a.diaper_type) details.push(this._diaperLabel(a.diaper_type));
              if (a.temperature_c != null) details.push(`${a.temperature_c}°C`);
              return `
                <div class="tl-item">
                  <div class="tl-body">
                    <div class="tl-head">
                      <span class="badge status-upcoming">${esc(this._kindLabel(a.kind))}</span>
                      ${details.length ? `<strong>${esc(details.join(" · "))}</strong>` : ""}
                      <span class="muted small">${esc(fmtTimestamp(a.timestamp))}</span>
                    </div>
                    ${a.note ? `<div class="tl-note">${esc(a.note)}</div>` : ""}
                    ${a.photo_url ? `<img src="${esc(a.photo_url)}" class="tl-photo" data-lightbox="${esc(a.photo_url)}" alt="photo" loading="lazy" />` : ""}
                  </div>
                  <button type="button" class="btn-outline small" data-del-activity="${esc(a.id)}" ${this._busy ? "disabled" : ""}>${esc(t.deleteChild)}</button>
                </div>`;
            })
            .join("");

      return `
        <div class="card section-card span-full" data-section="timeline">
          <h3>${esc(t.timelineTitle)}</h3>
          <div class="tabs">
            ${filters
              .map((f) => {
                const lbl = f === "all" ? t.filterAll : f === "photos" ? t.filterPhotos : this._kindLabel(f);
                return `<button type="button" class="tab ${this._timelineFilter === f ? "active" : ""}" data-tl-filter="${esc(f)}">${esc(lbl)}</button>`;
              })
              .join("")}
          </div>
          <div class="tl-list">${listHtml}</div>
        </div>`;
    }

    if (secId === "measurements") {
      return `
        <div class="card section-card" data-section="measurements">
          <h3>${esc(t.measurements)}</h3>
          <form id="measure-form">
            <div class="grid-4">
              <label>${esc(t.height)}
                <input name="height" type="number" step="0.1" min="30" max="200" value="${esc(child.inputs?.height?.value ?? "")}" />
                <span class="hint">${esc(child.inputs?.height?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.height?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.weight)}
                <input name="weight" type="number" step="0.05" min="1" max="100" value="${esc(child.inputs?.weight?.value ?? "")}" />
                <span class="hint">${esc(child.inputs?.weight?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.weight?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.head)}
                <input name="head" type="number" step="0.1" min="25" max="65" value="${esc(child.inputs?.head?.value ?? "")}" />
                <span class="hint">${esc(child.inputs?.head?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.head?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.measureDate)}
                <input name="date" type="date" value="${esc(child.today || "")}" />
                <span class="hint">&nbsp;</span>
              </label>
            </div>
            <div class="form-footer">
              <button type="submit" class="btn-primary" ${this._busy ? "disabled" : ""}>${esc(this._busy ? t.saving : t.saveMeasurement)}</button>
            </div>
          </form>
        </div>`;
    }

    if (secId === "growth") {
      const pcts = child.percentiles || {};
      const hInfo = pcts.height;
      const wInfo = pcts.weight;
      const headInfo = pcts.head;
      const bmiInfo = pcts.bmi;
      const wfl = child.weight_for_length;
      const sumKey = ko ? "summary_ko" : "summary_en";
      return `
        <div class="card section-card" data-section="growth">
          <h3>${esc(t.growthSummary)}</h3>
          ${
            !hInfo && !wInfo && !headInfo
              ? `<p class="muted">${esc(t.noMeasureYet)}</p>`
              : `
                <div class="grid-3">
                  <div class="stat">
                    <div class="muted small">${esc(t.height)}</div>
                    <div class="stat-val">${hInfo ? `${hInfo.value} cm` : "-"}</div>
                    <div class="muted small">${esc(hInfo?.[sumKey] || "")}</div>
                  </div>
                  <div class="stat">
                    <div class="muted small">${esc(t.weight)}</div>
                    <div class="stat-val">${wInfo ? `${wInfo.value} kg` : "-"}</div>
                    <div class="muted small">${esc(wInfo?.[sumKey] || "")}</div>
                  </div>
                  <div class="stat">
                    <div class="muted small">${esc(t.bmi)}</div>
                    <div class="stat-val">${child.bmi_raw != null ? `${child.bmi_raw} kg/m²` : "-"}</div>
                    <div class="muted small">${esc(bmiInfo?.[sumKey] || (child.bmi_age_months != null && child.bmi_age_months < 24 ? t.under24Note : ""))}</div>
                  </div>
                </div>
                <div class="concerns">
                  ${this._renderConcernBadge(t.concernHead, headInfo?.statistical_percentile, headInfo?.[sumKey])}
                  ${this._renderConcernBadge(t.concernBmi, bmiInfo?.statistical_percentile, bmiInfo?.[sumKey] || (child.age_months < 24 ? t.under24Note : ""))}
                  ${this._renderConcernBadge(t.concernWfl, wfl?.statistical_percentile, wfl?.[sumKey])}
                </div>`
          }
        </div>`;
    }

    if (secId === "tuition") {
      if (child.profile !== "kr" || !child.care_tuition) return "";
      return `
        <div class="card section-card" data-section="tuition">
          <h3>${esc(t.tuition)} <span class="muted small">(${esc(ko ? child.care_tuition.label_ko : child.care_tuition.label_en)})</span></h3>
          <div class="grid-3">
            <div class="stat">
              <div class="muted small">${esc(t.tuitionStd)}</div>
              <div class="stat-val">${Number(child.care_tuition.standard_tuition || 0).toLocaleString()} ${esc(t.won)}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.tuitionSub)}</div>
              <div class="stat-val">${Number(child.care_tuition.government_subsidy || 0).toLocaleString()} ${esc(t.won)}</div>
            </div>
            <div class="stat">
              <div class="muted small">${esc(t.tuitionShare)}</div>
              <div class="stat-val">${Number(child.care_tuition.parent_share || 0).toLocaleString()} ${esc(t.won)}</div>
            </div>
          </div>
        </div>`;
    }

    if (secId === "schedules") {
      return `
        <div class="card section-card span-full" data-section="schedules">
          <div class="card-head">
            <h3>${esc(t.schedules)}</h3>
            <label class="checkbox-label">
              <input type="checkbox" id="chk-show-past" ${this._showPast ? "checked" : ""} />
              ${esc(t.showPast)}
            </label>
          </div>
          <div class="tabs">
            <button class="tab ${this._scheduleTab === "vaccines" ? "active" : ""}" data-tab="vaccines">${esc(t.tabVaccines)}</button>
            <button class="tab ${this._scheduleTab === "checkups" ? "active" : ""}" data-tab="checkups">${esc(t.tabCheckups)}</button>
            <button class="tab ${this._scheduleTab === "oral" ? "active" : ""}" data-tab="oral">${esc(t.tabOral)}</button>
          </div>
          <div class="sched-list">
            ${this._renderScheduleList(child)}
          </div>
        </div>`;
    }
    return "";
  }

  _renderSettingsDrawer() {
    if (!this._settingsOpen) return "";
    const t = this._t();
    const ko = this._isKo();
    const secLabels = {
      care: t.secCare,
      timeline: t.secTimeline,
      measurements: t.secMeasurements,
      growth: t.secGrowth,
      tuition: t.secTuition,
      schedules: t.secSchedules,
    };

    const themeCards = THEMES.map((th) => {
      const active = this._prefs.theme === th.id;
      return `
        <button type="button" class="theme-card ${active ? "active" : ""}" data-select-theme="${esc(th.id)}">
          <div class="swatch" style="background:${esc(th.swatch.bg)};border-color:${esc(th.swatch.border)};">
            <div class="swatch-card" style="background:${esc(th.swatch.card)};border:1.5px solid ${esc(th.swatch.border)};border-radius:${esc(th.swatch.radius)};">
              <span class="swatch-bar" style="background:${esc(th.swatch.accent)};"></span>
              <span class="swatch-line"></span>
            </div>
          </div>
          <div class="theme-name">${esc(ko ? th.nameKo : th.nameEn)}</div>
          <div class="theme-desc">${esc(ko ? th.descKo : th.descEn)}</div>
        </button>`;
    }).join("");

    const sectionRows = this._prefs.order
      .map((secId, idx) => {
        const checked = this._prefs.visible[secId] ? "checked" : "";
        return `
          <div class="order-row">
            <label class="checkbox-label">
              <input type="checkbox" data-toggle-section="${esc(secId)}" ${checked} />
              <span>${esc(secLabels[secId] || secId)}</span>
            </label>
            <div class="order-btns">
              <button type="button" class="btn-outline small" data-move-sec="${esc(secId)}" data-dir="-1" ${idx === 0 ? "disabled" : ""}>&#8593;</button>
              <button type="button" class="btn-outline small" data-move-sec="${esc(secId)}" data-dir="1" ${idx === this._prefs.order.length - 1 ? "disabled" : ""}>&#8595;</button>
            </div>
          </div>`;
      })
      .join("");

    return `
      <div class="backdrop drawer-backdrop" id="settings-backdrop">
        <div class="drawer" role="dialog" aria-modal="true">
          <div class="drawer-head">
            <h3>${esc(t.settingsTitle)}</h3>
            <button type="button" class="btn-outline small" id="btn-close-settings">${esc(t.close)}</button>
          </div>
          <div class="drawer-body">
            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsTheme)}</div>
              <div class="theme-grid">${themeCards}</div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsLayout)}</div>
              <div class="seg-group">
                <button type="button" class="seg ${this._prefs.layout === "single" ? "active" : ""}" data-select-layout="single">${esc(t.layoutSingle)}</button>
                <button type="button" class="seg ${this._prefs.layout === "bento" ? "active" : ""}" data-select-layout="bento">${esc(t.layoutBento)}</button>
                <button type="button" class="seg ${this._prefs.layout === "compact" ? "active" : ""}" data-select-layout="compact">${esc(t.layoutCompact)}</button>
              </div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsSections)}</div>
              <div class="order-list">
                ${sectionRows}
                <div class="order-row">
                  <label class="checkbox-label">
                    <input type="checkbox" data-toggle-section="footer" ${this._prefs.visible.footer ? "checked" : ""} />
                    <span>${esc(t.secFooter)}</span>
                  </label>
                </div>
              </div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsDefaultTab)}</div>
              <div class="seg-group">
                <button type="button" class="seg ${this._prefs.defaultScheduleTab === "vaccines" ? "active" : ""}" data-default-tab="vaccines">${esc(t.tabVaccines)}</button>
                <button type="button" class="seg ${this._prefs.defaultScheduleTab === "checkups" ? "active" : ""}" data-default-tab="checkups">${esc(t.tabCheckups)}</button>
                <button type="button" class="seg ${this._prefs.defaultScheduleTab === "oral" ? "active" : ""}" data-default-tab="oral">${esc(t.tabOral)}</button>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-outline" id="btn-reset-prefs">${esc(t.resetPrefs)}</button>
            </div>
          </div>
        </div>
      </div>`;
  }

  _renderModal() {
    if (!this._modal) return "";
    const t = this._t();
    const isAdd = this._modal.mode === "add";
    const c = this._modal.child || {};
    const defaultProfile = this._isKo() ? "kr" : "global";
    const defaultBd = this._data?.default_birthdate || "2024-07-01";
    const name = isAdd ? "" : c.name || "";
    const bd = isAdd ? defaultBd : c.birthdate || defaultBd;
    const sex = isAdd ? "male" : c.sex || "male";
    const profile = isAdd ? defaultProfile : c.profile || "kr";

    return `
      <div class="backdrop" id="modal-backdrop">
        <div class="modal" role="dialog" aria-modal="true">
          <h3>${esc(isAdd ? t.modalAddTitle : t.modalEditTitle)}</h3>
          <form id="child-form">
            <label>${esc(t.name)}
              <input name="child_name" type="text" required placeholder="${esc(t.namePlaceholder)}" value="${esc(name)}" />
            </label>
            <label>${esc(t.birthdate)}
              <input name="child_birthdate" type="date" required value="${esc(bd)}" />
            </label>
            <label>${esc(t.sex)}
              <select name="child_sex">
                <option value="male" ${sex === "male" ? "selected" : ""}>${esc(t.male)}</option>
                <option value="female" ${sex === "female" ? "selected" : ""}>${esc(t.female)}</option>
              </select>
            </label>
            <label>${esc(t.profile)}
              <select name="profile">
                <option value="kr" ${profile === "kr" ? "selected" : ""}>${esc(t.profileKr)}</option>
                <option value="global" ${profile === "global" ? "selected" : ""}>${esc(t.profileGlobal)}</option>
              </select>
            </label>
            <div class="modal-actions">
              ${!isAdd ? `<button type="button" class="btn-danger" id="btn-delete-child" ${this._busy ? "disabled" : ""}>${esc(t.deleteChild)}</button>` : "<span></span>"}
              <div class="right-actions">
                <button type="button" class="btn-outline" id="btn-cancel-modal">${esc(t.cancel)}</button>
                <button type="submit" class="btn-primary" ${this._busy ? "disabled" : ""}>${esc(this._busy ? t.saving : t.save)}</button>
              </div>
            </div>
          </form>
        </div>
      </div>`;
  }

  _renderLightbox() {
    if (!this._lightboxUrl) return "";
    return `
      <div class="backdrop" id="lightbox-backdrop">
        <img src="${esc(this._lightboxUrl)}" class="lightbox-img" alt="photo" />
      </div>`;
  }

  _render() {
    const t = this._t();
    const children = this._data?.children || [];
    const child = this._currentChild();
    const layoutClass = `layout-${this._prefs.layout}`;
    const themeStyle = getThemeCss(this._prefs.theme);

    let bodyHtml = "";
    if (!child) {
      bodyHtml = `<div class="card"><p class="muted">${esc(t.noChildren)}</p></div>`;
    } else {
      const sexLabel = child.sex === "male" ? t.male : t.female;
      const profLabel = child.profile === "kr" ? "KR · KDCA" : "WHO";
      const initial = (child.name || "?").trim().slice(0, 1).toUpperCase();
      const sectionsHtml = this._prefs.order
        .map((secId) => this._renderSection(secId, child))
        .join("");

      bodyHtml = `
        <div class="card child-header">
          <div class="child-id-wrap">
            <label class="avatar-btn" title="${esc(t.changePhoto)}">
              ${
                child.avatar_url
                  ? `<img src="${esc(child.avatar_url)}" class="avatar-img" alt="${esc(child.name)}" />`
                  : `<span class="avatar-fallback">${esc(initial)}</span>`
              }
              <span class="avatar-cam">${CAM_SVG}</span>
              <input type="file" id="avatar-input" accept="image/*" hidden />
            </label>
            <div>
              <h2>${esc(child.name)}</h2>
              <div class="meta">
                <span>${esc(t.ageMonths(child.age_months))}</span>
                <span>·</span>
                <span>${esc(child.birthdate)}</span>
                <span>·</span>
                <span>${esc(sexLabel)}</span>
                <span class="badge neutral">${esc(profLabel)}</span>
              </div>
            </div>
          </div>
          <button class="btn-outline" id="btn-edit-child">${esc(t.editChild)}</button>
        </div>

        <div class="sections-wrap ${layoutClass}">
          ${sectionsHtml}
        </div>

        ${
          this._prefs.visible.footer
            ? `<p class="disclaimer">${esc(child.disclaimer || "")}<br/>${esc(child.attribution || "")}</p>`
            : ""
        }
      `;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ${themeStyle}
        :host {
          display: block;
          min-height: 100vh;
          background-color: var(--bk-bg);
          background-image: var(--bk-bg-image, none);
          background-size: var(--bk-bg-size, auto);
          color: var(--bk-text);
          font-family: var(--bk-font-body);
          transition: background-color 0.2s ease, color 0.2s ease;
        }
        * { box-sizing: border-box; }
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 12px 20px;
          background: var(--bk-header-bg);
          color: var(--bk-header-text);
          border-bottom: var(--bk-header-border);
          position: sticky;
          top: 0;
          z-index: 5;
        }
        .topbar-left, .topbar-right { display: flex; align-items: center; gap: 10px; }
        .menu-btn {
          background: transparent; border: none; color: inherit; font-size: 22px;
          cursor: pointer; padding: 4px 8px; display: ${this._narrow ? "inline-flex" : "none"};
        }
        .icon-btn {
          display: inline-flex; align-items: center; justify-content: center;
          width: 36px; height: 36px; border-radius: var(--bk-btn-radius);
          background: rgba(128, 128, 128, 0.16); color: inherit;
          border: 1px solid rgba(128, 128, 128, 0.25); cursor: pointer;
        }
        .topbar h1 { margin: 0; font-size: 20px; font-weight: 600; font-family: var(--bk-font-head); }
        .container {
          max-width: ${this._prefs.layout === "bento" ? "1180px" : "960px"};
          margin: 0 auto;
          padding: ${this._prefs.layout === "compact" ? "10px 12px" : "18px 16px"};
        }
        .child-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .pill {
          padding: 7px 14px; border-radius: var(--bk-pill-radius); border: var(--bk-card-border);
          background: var(--bk-card); color: var(--bk-text); cursor: pointer; font-size: 14px;
        }
        .pill.active { background: var(--bk-accent); color: var(--bk-accent-text); border-color: transparent; }
        .sections-wrap.layout-bento {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start;
        }
        .sections-wrap.layout-bento .span-full { grid-column: 1 / -1; }
        @media (max-width: 820px) { .sections-wrap.layout-bento { grid-template-columns: 1fr; } }
        .card {
          background: var(--bk-card); backdrop-filter: var(--bk-card-backdrop);
          -webkit-backdrop-filter: var(--bk-card-backdrop);
          border-radius: var(--bk-card-radius);
          padding: ${this._prefs.layout === "compact" ? "12px 14px" : "18px 20px"};
          margin-bottom: ${this._prefs.layout === "bento" ? "0" : this._prefs.layout === "compact" ? "10px" : "16px"};
          box-shadow: var(--bk-card-shadow); border: var(--bk-card-border);
        }
        .child-header {
          display: flex; align-items: center; justify-content: space-between;
          gap: 12px; flex-wrap: wrap; margin-bottom: 16px;
        }
        .child-id-wrap { display: flex; align-items: center; gap: 14px; }
        .avatar-btn {
          position: relative; width: 62px; height: 62px; border-radius: 50%;
          background: var(--bk-surface); border: 2px solid var(--bk-accent);
          display: flex; align-items: center; justify-content: center;
          cursor: pointer; overflow: hidden; flex-shrink: 0;
        }
        .avatar-img { width: 100%; height: 100%; object-fit: cover; }
        .avatar-fallback { font-size: 24px; font-weight: 700; color: var(--bk-accent); }
        .avatar-cam {
          position: absolute; bottom: 0; left: 0; right: 0; height: 22px;
          background: rgba(0, 0, 0, 0.45); color: #fff;
          display: flex; align-items: center; justify-content: center;
          opacity: 0; transition: opacity 0.15s ease;
        }
        .avatar-btn:hover .avatar-cam { opacity: 1; }
        h2 { margin: 0 0 6px; font-size: 20px; font-weight: 600; font-family: var(--bk-font-head); }
        h3 { margin: 0 0 12px; font-size: 16px; font-weight: 600; font-family: var(--bk-font-head); }
        .meta { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; color: var(--bk-muted); font-size: 14px; }
        .summary-strip {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
          gap: 8px; margin-bottom: 14px;
        }
        .timer-grid {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 10px; margin-bottom: 14px;
        }
        .timer-tile {
          padding: 10px 12px; border-radius: var(--bk-btn-radius);
          background: var(--bk-surface); border: 1px solid var(--bk-input-border);
          display: flex; flex-direction: column; gap: 8px;
        }
        .timer-tile.running { border-color: var(--bk-accent); box-shadow: 0 0 0 1px var(--bk-accent); }
        .timer-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
        .timer-name { font-size: 13px; font-weight: 600; }
        .timer-clock { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 15px; font-weight: 600; color: var(--bk-accent); }
        .timer-btns { display: flex; gap: 6px; }
        .care-form { display: flex; flex-direction: column; gap: 10px; }
        .photo-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .photo-upload-btn { display: inline-flex; flex-direction: row; align-items: center; gap: 6px; cursor: pointer; }
        .photo-preview-wrap { display: flex; align-items: center; gap: 8px; }
        .photo-preview { width: 52px; height: 52px; object-fit: cover; border-radius: 6px; border: 1px solid var(--bk-input-border); }
        .tl-list { display: flex; flex-direction: column; gap: 10px; }
        .tl-item {
          display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;
          padding: 10px 12px; border-radius: var(--bk-btn-radius); background: var(--bk-surface);
        }
        .tl-body { display: flex; flex-direction: column; gap: 6px; flex: 1; }
        .tl-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .tl-note { font-size: 14px; white-space: pre-wrap; line-height: 1.45; }
        .tl-photo {
          max-width: 240px; max-height: 180px; border-radius: 8px; object-fit: cover;
          cursor: zoom-in; border: 1px solid var(--bk-input-border);
        }
        .lightbox-img { max-width: 92vw; max-height: 90vh; border-radius: 10px; box-shadow: 0 12px 40px rgba(0,0,0,0.5); }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; }
        label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--bk-muted); }
        input, select, textarea {
          padding: ${this._prefs.layout === "compact" ? "6px 8px" : "9px 10px"};
          border-radius: var(--bk-btn-radius); border: 1px solid var(--bk-input-border);
          background: var(--bk-input-bg); color: var(--bk-text); font-size: 14px; font-family: inherit;
        }
        textarea { resize: vertical; }
        .hint { font-size: 11px; color: var(--bk-muted); }
        .form-footer { display: flex; justify-content: flex-end; margin-top: 12px; }
        .btn-primary, .btn-outline, .btn-danger, .btn-top {
          padding: 8px 14px; border-radius: var(--bk-btn-radius); font-size: 14px;
          cursor: pointer; border: 1px solid transparent; font-family: inherit;
        }
        .btn-primary { background: var(--bk-accent); color: var(--bk-accent-text); }
        .btn-top { background: rgba(255, 255, 255, 0.18); color: inherit; border-color: rgba(255, 255, 255, 0.35); }
        .btn-outline { background: transparent; color: var(--bk-text); border-color: var(--bk-input-border); }
        .btn-danger { background: transparent; color: var(--error-color, #db4437); border-color: var(--error-color, #db4437); }
        button:disabled { opacity: 0.45; cursor: not-allowed; }
        .small { font-size: 12px; padding: 5px 10px; }
        .muted { color: var(--bk-muted); }
        .stat {
          padding: ${this._prefs.layout === "compact" ? "8px 10px" : "11px 13px"};
          border-radius: var(--bk-btn-radius); background: var(--bk-surface);
        }
        .stat-val {
          font-size: ${this._prefs.layout === "compact" ? "15px" : "18px"};
          font-weight: 600; margin: 4px 0; font-family: var(--bk-font-num);
        }
        .concerns { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
        .concern-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 14px; }
        .concern-label { font-weight: 500; min-width: 105px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: var(--bk-pill-radius); font-size: 12px; font-weight: 500; }
        .badge.neutral { background: rgba(128, 128, 128, 0.16); }
        .badge.ok, .badge.status-done { background: rgba(76, 175, 80, 0.18); color: #2e7d32; }
        .badge.warn, .badge.status-open { background: rgba(255, 152, 0, 0.22); color: #d97706; }
        .badge.status-upcoming { background: rgba(3, 169, 244, 0.18); color: var(--bk-accent); }
        .badge.status-past { background: rgba(128, 128, 128, 0.16); color: var(--bk-muted); }
        .card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
        .card-head h3 { margin: 0; }
        .checkbox-label { flex-direction: row; align-items: center; gap: 6px; cursor: pointer; color: var(--bk-text); }
        .tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; border-bottom: 1px solid var(--bk-input-border); padding-bottom: 8px; }
        .tab {
          background: transparent; border: none; padding: 6px 11px; border-radius: var(--bk-btn-radius);
          cursor: pointer; color: var(--bk-muted); font-size: 13px; font-family: inherit;
        }
        .tab.active { background: var(--bk-accent); color: var(--bk-accent-text); }
        .sched-list { display: flex; flex-direction: column; gap: 8px; }
        .sched-item {
          display: flex; align-items: center; justify-content: space-between; gap: 10px;
          padding: ${this._prefs.layout === "compact" ? "7px 10px" : "10px 12px"};
          border-radius: var(--bk-btn-radius); background: var(--bk-surface);
        }
        .sched-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .banner { padding: 10px 14px; border-radius: var(--bk-btn-radius); margin-bottom: 12px; font-size: 14px; }
        .banner.error { background: rgba(219, 68, 55, 0.15); color: var(--error-color, #c62828); }
        .banner.notice { background: rgba(76, 175, 80, 0.15); color: #2e7d32; }
        .disclaimer { font-size: 12px; color: var(--bk-muted); text-align: center; margin: 18px 0 32px; line-height: 1.5; }
        .backdrop {
          position: fixed; inset: 0; background: rgba(0, 0, 0, 0.55);
          display: flex; align-items: center; justify-content: center; z-index: 50; padding: 16px;
        }
        .drawer-backdrop { justify-content: flex-end; padding: 0; }
        .drawer {
          background: var(--card-background-color, #ffffff); color: var(--primary-text-color, #212121);
          width: 100%; max-width: 440px; height: 100vh; display: flex; flex-direction: column;
          box-shadow: -8px 0 32px rgba(0, 0, 0, 0.25); font-family: system-ui, -apple-system, sans-serif;
        }
        .drawer-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
        .drawer-head h3 { margin: 0; font-family: inherit; }
        .drawer-body { flex: 1; overflow-y: auto; padding: 16px 20px 32px; display: flex; flex-direction: column; gap: 20px; }
        .drawer-label { font-size: 13px; font-weight: 600; color: var(--secondary-text-color, #555); margin-bottom: 8px; }
        .theme-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
        .theme-card {
          text-align: left; padding: 8px; border-radius: 10px; border: 1.5px solid var(--divider-color, #ddd);
          background: var(--primary-background-color, #fafafa); color: var(--primary-text-color, #212121);
          cursor: pointer; display: flex; flex-direction: column; gap: 5px;
        }
        .theme-card.active { border-color: var(--primary-color, #03a9f4); box-shadow: 0 0 0 2px rgba(3, 169, 244, 0.22); }
        .swatch { height: 44px; border-radius: 6px; border: 1px solid #ddd; padding: 6px; display: flex; align-items: center; }
        .swatch-card { width: 100%; height: 100%; padding: 5px 7px; display: flex; flex-direction: column; justify-content: center; gap: 4px; }
        .swatch-bar { display: block; width: 45%; height: 5px; border-radius: 3px; }
        .swatch-line { display: block; width: 75%; height: 3px; border-radius: 2px; background: rgba(128, 128, 128, 0.35); }
        .theme-name { font-size: 13px; font-weight: 600; }
        .theme-desc { font-size: 11px; color: var(--secondary-text-color, #666); line-height: 1.3; }
        .seg-group { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
        .seg {
          padding: 8px 6px; border-radius: 8px; border: 1px solid var(--divider-color, #ccc);
          background: transparent; color: var(--primary-text-color, #212121); font-size: 13px; cursor: pointer;
        }
        .seg.active { background: var(--primary-color, #03a9f4); color: #fff; border-color: transparent; }
        .order-list { display: flex; flex-direction: column; gap: 8px; }
        .order-row {
          display: flex; align-items: center; justify-content: space-between;
          padding: 8px 10px; border-radius: 8px; background: var(--primary-background-color, #f5f5f5);
        }
        .order-btns { display: flex; gap: 4px; }
        .drawer-footer { padding-top: 8px; border-top: 1px solid var(--divider-color, #e0e0e0); display: flex; justify-content: flex-end; }
        .modal {
          background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
          border-radius: 12px; padding: 20px; width: 100%; max-width: 420px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25); font-family: system-ui, -apple-system, sans-serif;
        }
        .modal form { display: flex; flex-direction: column; gap: 12px; }
        .modal-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
        .right-actions { display: flex; gap: 8px; }
      </style>

      <div class="topbar">
        <div class="topbar-left">
          <button class="menu-btn" id="btn-menu" aria-label="Menu">&#9776;</button>
          <h1>${esc(t.title)}</h1>
        </div>
        <div class="topbar-right">
          <button class="btn-top" id="btn-add-child">+ ${esc(t.addChild)}</button>
          <button class="icon-btn" id="btn-open-settings" title="${esc(t.settingsTitle)}" aria-label="${esc(t.settingsTitle)}">${GEAR_SVG}</button>
        </div>
      </div>

      <div class="container">
        ${this._error ? `<div class="banner error">${esc(this._error)}</div>` : ""}
        ${this._notice ? `<div class="banner notice">${esc(this._notice)}</div>` : ""}

        ${
          children.length > 0
            ? `<div class="child-pills">${children
                .map(
                  (c) =>
                    `<button class="pill ${c.entry_id === child?.entry_id ? "active" : ""}" data-select-child="${esc(c.entry_id)}">${esc(c.name)}</button>`
                )
                .join("")}</div>`
            : ""
        }

        ${bodyHtml}
      </div>

      ${this._renderModal()}
      ${this._renderSettingsDrawer()}
      ${this._renderLightbox()}
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.getElementById("btn-menu")?.addEventListener("click", () => this._openSidebar());
    root.getElementById("btn-add-child")?.addEventListener("click", () => {
      this._modal = { mode: "add" };
      this._error = null;
      this._render();
    });
    root.getElementById("avatar-input")?.addEventListener("change", (e) => {
      const f = e.target.files?.[0];
      if (f) this._uploadAvatar(f);
    });
    root.querySelectorAll("[data-start-timer]").forEach((btn) => {
      btn.addEventListener("click", () => this._startTimer(btn.getAttribute("data-start-timer")));
    });
    root.querySelectorAll("[data-stop-timer]").forEach((btn) => {
      btn.addEventListener("click", () => this._stopTimer(btn.getAttribute("data-stop-timer"), true));
    });
    root.querySelectorAll("[data-cancel-timer]").forEach((btn) => {
      btn.addEventListener("click", () => this._stopTimer(btn.getAttribute("data-cancel-timer"), false));
    });
    root.querySelectorAll("[data-care-kind]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._careKind = btn.getAttribute("data-care-kind");
        this._render();
      });
    });
    root.getElementById("care-photo-input")?.addEventListener("change", async (e) => {
      const f = e.target.files?.[0];
      if (!f) return;
      try {
        this._pendingPhoto = await compressImage(f, 1280, 0.82);
        this._error = null;
      } catch (err) {
        this._error = err?.message || String(err);
      }
      this._render();
    });
    root.getElementById("btn-remove-photo")?.addEventListener("click", () => {
      this._pendingPhoto = null;
      this._render();
    });
    root.getElementById("care-form")?.addEventListener("submit", (e) => this._saveActivity(e));
    root.querySelectorAll("[data-tl-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._timelineFilter = btn.getAttribute("data-tl-filter");
        this._render();
      });
    });
    root.querySelectorAll("[data-del-activity]").forEach((btn) => {
      btn.addEventListener("click", () => this._deleteActivity(btn.getAttribute("data-del-activity")));
    });
    root.querySelectorAll("[data-lightbox]").forEach((img) => {
      img.addEventListener("click", () => {
        this._lightboxUrl = img.getAttribute("data-lightbox");
        this._render();
      });
    });
    root.getElementById("lightbox-backdrop")?.addEventListener("click", () => {
      this._lightboxUrl = null;
      this._render();
    });
    root.getElementById("btn-open-settings")?.addEventListener("click", () => {
      this._settingsOpen = true;
      this._render();
    });
    root.getElementById("btn-close-settings")?.addEventListener("click", () => {
      this._settingsOpen = false;
      this._render();
    });
    root.getElementById("settings-backdrop")?.addEventListener("click", (e) => {
      if (e.target.id === "settings-backdrop") {
        this._settingsOpen = false;
        this._render();
      }
    });
    root.querySelectorAll("[data-select-theme]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-select-theme");
        this._updatePrefs((p) => { p.theme = id; });
      });
    });
    root.querySelectorAll("[data-select-layout]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-select-layout");
        this._updatePrefs((p) => { p.layout = mode; });
      });
    });
    root.querySelectorAll("[data-toggle-section]").forEach((chk) => {
      chk.addEventListener("change", () => {
        const sec = chk.getAttribute("data-toggle-section");
        this._updatePrefs((p) => { p.visible[sec] = chk.checked; });
      });
    });
    root.querySelectorAll("[data-move-sec]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sec = btn.getAttribute("data-move-sec");
        const dir = Number(btn.getAttribute("data-dir"));
        this._updatePrefs((p) => {
          const i = p.order.indexOf(sec);
          const j = i + dir;
          if (i >= 0 && j >= 0 && j < p.order.length) {
            [p.order[i], p.order[j]] = [p.order[j], p.order[i]];
          }
        });
      });
    });
    root.querySelectorAll("[data-default-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-default-tab");
        this._scheduleTab = tab;
        this._updatePrefs((p) => { p.defaultScheduleTab = tab; });
      });
    });
    root.getElementById("btn-reset-prefs")?.addEventListener("click", () => {
      this._prefs = structuredClone(DEFAULT_PREFS);
      this._scheduleTab = DEFAULT_PREFS.defaultScheduleTab;
      savePrefs(this._prefs);
      this._render();
    });
    root.getElementById("btn-edit-child")?.addEventListener("click", () => {
      const child = this._currentChild();
      if (child) {
        this._modal = { mode: "edit", child };
        this._error = null;
        this._render();
      }
    });
    root.querySelectorAll("[data-select-child]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._selectedId = btn.getAttribute("data-select-child");
        this._pendingPhoto = null;
        this._render();
      });
    });
    root.getElementById("measure-form")?.addEventListener("submit", (e) => this._saveMeasurement(e));
    root.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._scheduleTab = btn.getAttribute("data-tab");
        this._render();
      });
    });
    root.getElementById("chk-show-past")?.addEventListener("change", (e) => {
      this._showPast = e.target.checked;
      this._render();
    });
    root.querySelectorAll("[data-toggle-done]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._toggleDone(
          btn.getAttribute("data-toggle-done"),
          btn.getAttribute("data-is-done") === "1"
        );
      });
    });
    root.getElementById("btn-cancel-modal")?.addEventListener("click", () => {
      this._modal = null;
      this._render();
    });
    root.getElementById("modal-backdrop")?.addEventListener("click", (e) => {
      if (e.target.id === "modal-backdrop") {
        this._modal = null;
        this._render();
      }
    });
    root.getElementById("child-form")?.addEventListener("submit", (e) => this._submitModal(e));
    root.getElementById("btn-delete-child")?.addEventListener("click", () => this._deleteChild());
  }
}

if (!customElements.get("kr-baby-kit-panel")) {
  customElements.define("kr-baby-kit-panel", KrBabyKitPanel);
}
