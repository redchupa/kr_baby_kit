/* Home Assistant Sidebar Panel for Baby Kit (kr_baby_kit) */
import { THEMES, getThemeCss } from "./themes.js?v=0.19.0";
import {
  CARD_STYLES,
  ICONS,
  cardStyleCss,
  renderPercentileGauge,
  renderSparkline,
} from "./cards.js?v=0.19.0";
import {
  renderGrowthCurveChart,
  renderWeeklyCareChart,
} from "./charts.js?v=0.19.0";
import {
  AUTOMATION_RECIPES,
  LAYOUT_MODES,
  renderAutomationsSection,
} from "./automations.js?v=0.19.0";
import {
  LANGUAGES,
  VALID_LANG_PREFS,
  fmtAgoI18n,
  fmtMinutesI18n,
  getLangMeta,
  getStrings,
  resolveLang,
} from "./i18n.js?v=0.19.0";

const PREFS_KEY = "kr_baby_kit_panel_prefs_v4";

const DEFAULT_PREFS = {
  lang: "auto", // "auto" | "ko" | "en" | "ja" | "zh-Hans" | "es" | "fr" | "de" | "pt"
  theme: "nordic-nursery",
  cardStyle: "bubble", // "bubble" | "mushroom" | "bento-pro" | "classic"
  layout: "bento", // 8 layout modes in LAYOUT_MODES
  mobileCols: 2, // 2 | 3 | 4 (mobile micro-tile density)
  order: ["care", "growth", "measurements", "timeline", "schedules", "tuition", "automations"],
  visible: {
    chips: true,
    care: true,
    growth: true,
    measurements: true,
    timeline: true,
    tuition: true,
    schedules: true,
    automations: true,
    footer: true,
  },
  wide: {
    care: false,
    growth: false,
    measurements: false,
    timeline: false,
    tuition: false,
    schedules: false,
    automations: true,
  },
  defaultScheduleTab: "vaccines",
};

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

function fmtTimestamp(iso) {
  if (!iso) return "";
  return String(iso).replace("T", " ").slice(0, 16);
}

function daysBetween(fromIso, toIso) {
  if (!fromIso || !toIso) return null;
  const a = Date.parse(fromIso);
  const b = Date.parse(toIso);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.round((b - a) / 86400000);
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
      lang: VALID_LANG_PREFS.includes(parsed.lang) ? parsed.lang : DEFAULT_PREFS.lang,
      theme: THEMES.some((t) => t.id === parsed.theme) ? parsed.theme : DEFAULT_PREFS.theme,
      cardStyle: CARD_STYLES.some((c) => c.id === parsed.cardStyle)
        ? parsed.cardStyle
        : DEFAULT_PREFS.cardStyle,
      layout: LAYOUT_MODES.some((l) => l.id === parsed.layout)
        ? parsed.layout
        : DEFAULT_PREFS.layout,
      mobileCols: [2, 3, 4].includes(Number(parsed.mobileCols))
        ? Number(parsed.mobileCols)
        : DEFAULT_PREFS.mobileCols,
      order: validOrder,
      visible: { ...DEFAULT_PREFS.visible, ...(parsed.visible || {}) },
      wide: { ...DEFAULT_PREFS.wide, ...(parsed.wide || {}) },
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
    this._mobileNav = "all"; // "all" | "care" | "growth" | "diary" | "schedule"
    this._careKind = "note";
    this._careModalOpen = false;
    this._careDraft = this._emptyCareDraft();
    this._measureDraft = {};
    this._growthChartKind = "height"; // "height" | "weight"
    this._openRecipeId = null;
    this._copiedRecipeId = null;
    this._appDeckTab = "care";
    this._timelineFilter = "all";
    this._pendingPhoto = null;
    this._lightboxUrl = null;
    this._showPast = false;
    this._expandSchedule = false;
    this._modal = null;
    this._settingsOpen = false;
    this._settingsDraft = null;
    this._langMenuOpen = false;
    this._busy = false;
    this._notice = null;
    this._error = null;
    this._tickHandle = null;
  }

  connectedCallback() {
    if (!this._tickHandle) {
      this._tickHandle = window.setInterval(() => this._tickTimers(), 1000);
    }
    if (!this._onResize) {
      this._onResize = () => {
        const isMobile = Boolean(window.matchMedia?.("(max-width: 920px)")?.matches);
        if (this._lastMobileMatch !== isMobile) {
          this._lastMobileMatch = isMobile;
          this._render();
        }
      };
      window.addEventListener?.("resize", this._onResize);
    }
  }

  disconnectedCallback() {
    if (this._tickHandle) {
      window.clearInterval(this._tickHandle);
      this._tickHandle = null;
    }
    if (this._onResize) {
      window.removeEventListener?.("resize", this._onResize);
      this._onResize = null;
    }
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._load();
  }

  set narrow(val) {
    this._narrow = Boolean(val);
    this._render();
  }

  _emptyCareDraft() {
    return {
      method: "formula",
      amount_ml: "",
      duration_min: "",
      diaper_type: "wet",
      temperature_c: "",
      note: "",
    };
  }

  _lang() {
    return resolveLang(this._prefs?.lang, this._hass?.language || this._data?.language);
  }

  _isKo() {
    return this._lang() === "ko";
  }

  _t() {
    return getStrings(this._lang());
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

  _updateSettingsDraft(mutator) {
    const next = structuredClone(this._settingsDraft || this._prefs);
    mutator(next);
    this._settingsDraft = next;
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
    }, 2200);
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

  async _quickLog(kind, extra = {}) {
    const child = this._currentChild();
    if (!child || this._busy) return;
    this._busy = true;
    this._error = null;
    this._render();
    try {
      await this._hass.callWS({
        type: "kr_baby_kit/add_activity",
        child_id: child.child_id,
        kind,
        ...extra,
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
      this._careDraft = this._emptyCareDraft();
      this._careModalOpen = false;
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
      delete this._measureDraft[child.child_id];
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

  _renderStatusChips(child) {
    if (!this._prefs.visible.chips) return "";
    const t = this._t();
    const lang = this._lang();
    const sum = child.today_summary || {};
    const vacs = child.vaccines || [];
    const chks = child.checkups || [];
    const openVac = vacs.find((e) => e.status === "open");
    const nextVac = vacs.find((e) => e.status === "upcoming");
    const openChk = chks.find((e) => e.status === "open");
    const nextChk = chks.find((e) => e.status === "upcoming");

    const pcts = child.percentiles || {};
    const anyWarn = [
      pcts.head?.statistical_percentile,
      pcts.bmi?.statistical_percentile,
      child.weight_for_length?.statistical_percentile,
    ].some((v) => v != null && (v < 5 || v > 95));

    const chips = [];
    if (openVac) {
      chips.push(`<span class="chip tone-amber">${ICONS.vaccine}<span>${esc(t.chipOpenVac)}</span></span>`);
    } else if (nextVac) {
      const d = daysBetween(child.today, nextVac.window_start);
      if (d != null) chips.push(`<span class="chip tone-blue">${ICONS.vaccine}<span>${esc(t.chipNextVac(d))}</span></span>`);
    }
    if (openChk) {
      chips.push(`<span class="chip tone-amber">${ICONS.checkup}<span>${esc(t.chipOpenChk)}</span></span>`);
    } else if (nextChk) {
      const d = daysBetween(child.today, nextChk.window_start);
      if (d != null) chips.push(`<span class="chip tone-teal">${ICONS.checkup}<span>${esc(t.chipNextChk(d))}</span></span>`);
    }
    chips.push(`<span class="chip tone-indigo">${ICONS.sleep}<span>${esc(fmtMinutesI18n(sum.sleep_min, lang))}</span></span>`);
    chips.push(`<span class="chip tone-sky">${ICONS.feeding}<span>${sum.feeding_count || 0}${esc(t.countUnit)}${sum.feeding_ml ? ` · ${sum.feeding_ml}ml` : ""}</span></span>`);
    chips.push(`<span class="chip ${anyWarn ? "tone-rose" : "tone-green"}">${ICONS.shield}<span>${esc(anyWarn ? t.concernWarn : t.concernOk)}</span></span>`);

    return `<div class="chips-bar">${chips.join("")}</div>`;
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

    if (!filtered.length) return `<p class="muted">-</p>`;
    const limit = this._expandSchedule ? 30 : 5;
    const shown = filtered.slice(0, limit);
    const rows = shown
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
        const icon = this._scheduleTab === "vaccines" ? ICONS.vaccine : ICONS.checkup;
        return `
          <div class="sched-item">
            <div class="sched-left">
              <div class="icon-well tone-${e.status === "open" ? "amber" : e.status === "done" ? "green" : "blue"}">${icon}</div>
              <div class="sched-meta">
                <div class="sched-title">
                  <strong>${esc(name + dose)}</strong>
                  <span class="badge status-${esc(e.status)}">${esc(statusLabel)}</span>
                </div>
                <div class="sched-date">${esc(e.window_start)} ~ ${esc(e.window_end)}${e.completed_date ? ` (${esc(e.completed_date)})` : ""}</div>
              </div>
            </div>
            <button class="btn-outline small" data-toggle-done="${esc(e.event_id)}" data-is-done="${isDone ? "1" : "0"}" ${this._busy ? "disabled" : ""}>${esc(isDone ? t.unmarkDone : t.markDone)}</button>
          </div>`;
      })
      .join("");
    const toggleBtn =
      filtered.length > 5
        ? `<button type="button" class="btn-outline small expand-btn" id="btn-expand-sched">${esc(this._expandSchedule ? t.showLessSched : t.showAllSched(filtered.length))}</button>`
        : "";
    return rows + toggleBtn;
  }

  _renderCareFormFields() {
    const t = this._t();
    const k = this._careKind;
    const d = this._careDraft || this._emptyCareDraft();
    if (k === "feeding") {
      return `
        <div class="grid-3">
          <label>${esc(t.methodLabel)}
            <select name="method" data-care-field="method">
              <option value="formula" ${d.method === "formula" ? "selected" : ""}>${esc(t.methodFormula)}</option>
              <option value="bottle" ${d.method === "bottle" ? "selected" : ""}>${esc(t.methodBottle)}</option>
              <option value="breast_left" ${d.method === "breast_left" ? "selected" : ""}>${esc(t.methodBreastL)}</option>
              <option value="breast_right" ${d.method === "breast_right" ? "selected" : ""}>${esc(t.methodBreastR)}</option>
              <option value="breast_both" ${d.method === "breast_both" ? "selected" : ""}>${esc(t.methodBreastB)}</option>
              <option value="solid" ${d.method === "solid" ? "selected" : ""}>${esc(t.methodSolid)}</option>
            </select>
          </label>
          <label>${esc(t.amountMl)}
            <input name="amount_ml" data-care-field="amount_ml" type="number" step="5" min="0" max="1000" placeholder="140" value="${esc(d.amount_ml)}" />
          </label>
          <label>${esc(t.durationMin)}
            <input name="duration_min" data-care-field="duration_min" type="number" step="1" min="0" max="300" placeholder="15" value="${esc(d.duration_min)}" />
          </label>
        </div>`;
    }
    if (k === "sleep" || k === "tummy_time") {
      return `
        <div class="grid-3">
          <label>${esc(t.durationMin)}
            <input name="duration_min" data-care-field="duration_min" type="number" step="1" min="1" max="1440" placeholder="${k === "sleep" ? "90" : "15"}" value="${esc(d.duration_min)}" />
          </label>
        </div>`;
    }
    if (k === "diaper") {
      return `
        <div class="grid-3">
          <label>${esc(t.diaperType)}
            <select name="diaper_type" data-care-field="diaper_type">
              <option value="wet" ${d.diaper_type === "wet" ? "selected" : ""}>${esc(t.wet)}</option>
              <option value="solid" ${d.diaper_type === "solid" ? "selected" : ""}>${esc(t.solid)}</option>
              <option value="both" ${d.diaper_type === "both" ? "selected" : ""}>${esc(t.both)}</option>
            </select>
          </label>
        </div>`;
    }
    if (k === "pumping") {
      return `
        <div class="grid-3">
          <label>${esc(t.amountMl)}
            <input name="amount_ml" data-care-field="amount_ml" type="number" step="5" min="0" max="1000" placeholder="120" value="${esc(d.amount_ml)}" />
          </label>
          <label>${esc(t.durationMin)}
            <input name="duration_min" data-care-field="duration_min" type="number" step="1" min="0" max="180" placeholder="20" value="${esc(d.duration_min)}" />
          </label>
        </div>`;
    }
    if (k === "temperature") {
      return `
        <div class="grid-3">
          <label>${esc(t.tempC)}
            <input name="temperature_c" data-care-field="temperature_c" type="number" step="0.1" min="34" max="43" placeholder="36.7" value="${esc(d.temperature_c)}" required />
          </label>
        </div>`;
    }
    return "";
  }

  _renderSection(secId, child) {
    const t = this._t();
    const lang = this._lang();
    const ko = lang === "ko";
    if (!this._prefs.visible[secId]) return "";
    const wideClass = this._prefs.wide[secId] ? "span-full" : "";

    if (secId === "care") {
      const sum = child.today_summary || {};
      const timers = child.timers || {};
      const timerDefs = [
        { k: "sleep", tone: "indigo" },
        { k: "feeding", tone: "sky" },
        { k: "tummy_time", tone: "green" },
        { k: "pumping", tone: "rose" },
      ];
      const logKinds = ["note", "feeding", "sleep", "diaper", "tummy_time", "pumping", "temperature"];

      const timerCards = timerDefs
        .map(({ k, tone }) => {
          const active = Boolean(timers[k]?.started_at);
          return `
            <div class="timer-tile ${active ? "running" : ""}">
              <div class="timer-left">
                <div class="icon-well tone-${tone}">${ICONS[k]}</div>
                <div>
                  <div class="timer-name">${active ? `<span class="pulse-dot"></span>` : ""}${esc(this._kindLabel(k))}</div>
                  <div class="timer-clock" data-timer-clock="${esc(k)}">${active ? esc(fmtElapsed(timers[k].started_at)) : "00:00:00"}</div>
                </div>
              </div>
              <div class="timer-btns">
                ${
                  active
                    ? `<button type="button" class="sub-btn primary" data-stop-timer="${esc(k)}" title="${esc(t.timerStop)}" ${this._busy ? "disabled" : ""}>${ICONS.stop}</button>
                       <button type="button" class="btn-outline small" data-cancel-timer="${esc(k)}" ${this._busy ? "disabled" : ""}>${esc(t.timerCancel)}</button>`
                    : `<button type="button" class="sub-btn" data-start-timer="${esc(k)}" title="${esc(t.timerStart)}" ${this._busy ? "disabled" : ""}>${ICONS.play}</button>`
                }
              </div>
            </div>`;
        })
        .join("");

      return `
        <div class="card section-card ${wideClass}" data-section="care">
          <div class="card-head">
            <h3>${esc(t.careTitle)}</h3>
            <div class="quick-bar">
              <button type="button" class="quick-pill" data-quick-log="wet" ${this._busy ? "disabled" : ""}>${esc(t.quickWet)}</button>
              <button type="button" class="quick-pill" data-quick-log="solid" ${this._busy ? "disabled" : ""}>${esc(t.quickSolid)}</button>
              <button type="button" class="quick-pill" data-quick-log="feed140" ${this._busy ? "disabled" : ""}>${esc(t.quickFeed)}</button>
              <button type="button" class="quick-pill" data-quick-log="tummy10" ${this._busy ? "disabled" : ""}>${esc(t.quickTummy)}</button>
            </div>
          </div>

          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="icon-well tone-indigo">${ICONS.sleep}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todaySleep)}</div>
                <div class="kpi-val">${esc(fmtMinutesI18n(sum.sleep_min, lang))}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-sky">${ICONS.feeding}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todayFeed)}${child.last_care?.feeding?.timestamp ? ` · <span class="kpi-ago">${esc(fmtAgoI18n(child.last_care.feeding.timestamp, lang))}</span>` : ""}</div>
                <div class="kpi-val">${sum.feeding_count || 0}${esc(t.countUnit)}${sum.feeding_ml ? ` · ${sum.feeding_ml}ml` : ""}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-amber">${ICONS.diaper}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todayDiaper)}${child.last_care?.diaper?.timestamp ? ` · <span class="kpi-ago">${esc(fmtAgoI18n(child.last_care.diaper.timestamp, lang))}</span>` : ""}</div>
                <div class="kpi-val">${esc(t.wet)} ${sum.diaper_wet || 0} · ${esc(t.solid)} ${sum.diaper_solid || 0}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-green">${ICONS.tummy_time}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todayTummy)}</div>
                <div class="kpi-val">${esc(fmtMinutesI18n(sum.tummy_min, lang))}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-rose">${ICONS.temperature}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todayTemp)}</div>
                <div class="kpi-val">${sum.last_temp_c != null ? `${sum.last_temp_c}°C` : "-"}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-teal">${ICONS.camera}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.todayPhotos)}</div>
                <div class="kpi-val">${sum.photo_count || 0}${esc(t.photoUnit)}</div>
              </div>
            </div>
          </div>

          <div class="timer-grid">${timerCards}</div>

          <div class="care-launcher-box">
            <div class="care-launcher-head">
              <strong class="launcher-title">${esc(t.logDetailTitle)}</strong>
              <span class="launcher-sub">${esc(t.logDetailSub)}</span>
            </div>
            <div class="care-launcher-grid">
              ${logKinds
                .map((lk) => {
                  const toneMap = {
                    note: "teal",
                    feeding: "sky",
                    sleep: "indigo",
                    diaper: "amber",
                    tummy_time: "green",
                    pumping: "rose",
                    temperature: "rose",
                  };
                  return `
                    <button type="button" class="care-launch-btn" data-open-care="${esc(lk)}" ${this._busy ? "disabled" : ""}>
                      <span class="icon-well tone-${toneMap[lk] || "blue"}">${ICONS[lk] || ICONS.note}</span>
                      <span>${esc(this._kindLabel(lk))}</span>
                    </button>`;
                })
                .join("")}
            </div>
          </div>

          ${renderWeeklyCareChart(child.weekly_care, { ko, t })}
        </div>`;
    }

    if (secId === "timeline") {
      const items = child.activities || [];
      const photos = items.filter((a) => a.photo_url).slice(0, 12);
      const filters = ["all", "photos", "feeding", "sleep", "diaper", "tummy_time", "temperature", "note"];
      const filtered = items.filter((a) => {
        if (this._timelineFilter === "all") return true;
        if (this._timelineFilter === "photos") return Boolean(a.photo_url);
        return a.kind === this._timelineFilter;
      });

      const galleryHtml = photos.length
        ? `<div class="photo-strip">${photos
            .map(
              (p) =>
                `<img src="${esc(p.photo_url)}" class="strip-thumb" data-lightbox="${esc(p.photo_url)}" alt="photo" loading="lazy" />`
            )
            .join("")}</div>`
        : "";

      const listHtml = !filtered.length
        ? `<p class="muted">${esc(t.noActivities)}</p>`
        : filtered
            .slice(0, 40)
            .map((a) => {
              const details = [];
              if (a.method) details.push(this._methodLabel(a.method));
              if (a.amount_ml != null) details.push(`${a.amount_ml} ml`);
              if (a.duration_min != null) details.push(fmtMinutesI18n(a.duration_min, lang));
              if (a.diaper_type) details.push(this._diaperLabel(a.diaper_type));
              if (a.temperature_c != null) details.push(`${a.temperature_c}°C`);
              const toneMap = {
                sleep: "indigo", feeding: "sky", diaper: "amber",
                tummy_time: "green", pumping: "rose", temperature: "rose", note: "teal",
              };
              return `
                <div class="tl-item">
                  <div class="icon-well tone-${toneMap[a.kind] || "blue"}">${ICONS[a.kind] || ICONS.note}</div>
                  <div class="tl-body">
                    <div class="tl-head">
                      <strong>${esc(this._kindLabel(a.kind))}</strong>
                      ${details.length ? `<span class="badge neutral">${esc(details.join(" · "))}</span>` : ""}
                      <span class="tl-time">${esc(fmtTimestamp(a.timestamp))}</span>
                    </div>
                    ${a.note ? `<div class="tl-note">${esc(a.note)}</div>` : ""}
                    ${a.photo_url ? `<img src="${esc(a.photo_url)}" class="tl-photo" data-lightbox="${esc(a.photo_url)}" alt="photo" loading="lazy" />` : ""}
                  </div>
                  <button type="button" class="btn-outline small" data-del-activity="${esc(a.id)}" ${this._busy ? "disabled" : ""}>${esc(t.deleteChild)}</button>
                </div>`;
            })
            .join("");

      return `
        <div class="card section-card ${wideClass}" data-section="timeline">
          <h3>${esc(t.timelineTitle)}</h3>
          ${galleryHtml}
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
      const mDraft = this._measureDraft[child.child_id] || {};
      const hVal = mDraft.height ?? child.inputs?.height?.value ?? "";
      const wVal = mDraft.weight ?? child.inputs?.weight?.value ?? "";
      const headVal = mDraft.head ?? child.inputs?.head?.value ?? "";
      const dateVal = mDraft.date ?? child.today ?? "";
      return `
        <div class="card section-card ${wideClass}" data-section="measurements">
          <h3>${esc(t.measurements)}</h3>
          <form id="measure-form">
            <div class="grid-2">
              <label>${esc(t.height)}
                <input name="height" data-measure-field="height" type="number" step="0.1" min="30" max="200" value="${esc(hVal)}" />
                <span class="hint">${esc(child.inputs?.height?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.height?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.weight)}
                <input name="weight" data-measure-field="weight" type="number" step="0.05" min="1" max="100" value="${esc(wVal)}" />
                <span class="hint">${esc(child.inputs?.weight?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.weight?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.head)}
                <input name="head" data-measure-field="head" type="number" step="0.1" min="25" max="65" value="${esc(headVal)}" />
                <span class="hint">${esc(child.inputs?.head?.is_default_median ? t.defaultMedian : t.recordedAt(child.inputs?.head?.measured_at || ""))}</span>
              </label>
              <label>${esc(t.measureDate)}
                <input name="date" data-measure-field="date" type="date" value="${esc(dateVal)}" />
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
      const hSpark = renderSparkline(child.records, "height", "cm");
      const wSpark = renderSparkline(child.records, "weight", "kg");
      const cKind = this._growthChartKind === "weight" ? "weight" : "height";
      const curveSvg = renderGrowthCurveChart(
        child.growth_curves?.[cKind],
        child.age_months,
        { unit: cKind === "weight" ? "kg" : "cm", ko, t }
      );

      const gaugeItem = (icon, tone, title, valText, pct, summary, warnBand = false) => `
        <div class="gauge-card">
          <div class="gauge-top">
            <div class="icon-well tone-${tone}">${icon}</div>
            <div class="kpi-body gauge-meta">
              <div class="kpi-label">${esc(title)}</div>
              <div class="kpi-val">${esc(valText)}</div>
            </div>
            ${
              pct != null
                ? `<span class="badge ${warnBand && (pct < 5 || pct > 95) ? "warn" : "ok"}">${pct.toFixed(1)}%</span>`
                : ""
            }
          </div>
          ${renderPercentileGauge(pct, { warnBand })}
          ${summary ? `<div class="gauge-summary">${esc(summary)}</div>` : ""}
        </div>`;

      return `
        <div class="card section-card ${wideClass}" data-section="growth">
          <div class="card-head">
            <h3>${esc(t.growthSummary)}</h3>
            <div class="curve-tabs">
              <button type="button" class="quick-pill ${cKind === "height" ? "active-pill" : ""}" data-curve-kind="height">${esc(t.curveHeight)}</button>
              <button type="button" class="quick-pill ${cKind === "weight" ? "active-pill" : ""}" data-curve-kind="weight">${esc(t.curveWeight)}</button>
            </div>
          </div>
          ${curveSvg}
          ${
            !hInfo && !wInfo && !headInfo
              ? `<p class="muted" style="margin-top:10px;">${esc(t.noMeasureYet)}</p>`
              : `
                <div class="gauge-grid" style="margin-top:12px;">
                  ${gaugeItem(ICONS.ruler, "blue", t.height, hInfo ? `${hInfo.value} cm` : "-", hInfo?.statistical_percentile, hInfo?.[sumKey])}
                  ${gaugeItem(ICONS.scale, "teal", t.weight, wInfo ? `${wInfo.value} kg` : "-", wInfo?.statistical_percentile, wInfo?.[sumKey])}
                  ${gaugeItem(ICONS.shield, "indigo", t.concernHead, headInfo ? `${headInfo.value} cm` : "-", headInfo?.statistical_percentile, headInfo?.[sumKey], true)}
                  ${gaugeItem(
                    ICONS.checkup,
                    "amber",
                    child.age_months < 24 ? t.concernWfl : t.bmi,
                    child.age_months < 24
                      ? (wfl ? `${wfl.weight_kg} kg` : "-")
                      : (child.bmi_raw != null ? `${child.bmi_raw} kg/m²` : "-"),
                    child.age_months < 24 ? wfl?.statistical_percentile : bmiInfo?.statistical_percentile,
                    child.age_months < 24 ? wfl?.[sumKey] : (bmiInfo?.[sumKey] || t.under24Note),
                    true
                  )}
                </div>
                ${hSpark || wSpark ? `<div class="spark-grid">${hSpark}${wSpark}</div>` : ""}`
          }
        </div>`;
    }

    if (secId === "tuition") {
      if (child.profile !== "kr" || !child.care_tuition) return "";
      return `
        <div class="card section-card ${wideClass}" data-section="tuition">
          <div class="card-head">
            <h3>${esc(t.tuition)}</h3>
            <span class="sub-badge">${esc(ko ? child.care_tuition.label_ko : child.care_tuition.label_en)}</span>
          </div>
          <div class="kpi-grid tuition-grid">
            <div class="kpi-card">
              <div class="icon-well tone-blue">${ICONS.wallet}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.tuitionStd)}</div>
                <div class="kpi-val">${Number(child.care_tuition.standard_tuition || 0).toLocaleString()} ${esc(t.won)}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-teal">${ICONS.shield}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.tuitionSub)}</div>
                <div class="kpi-val">${Number(child.care_tuition.government_subsidy || 0).toLocaleString()} ${esc(t.won)}</div>
              </div>
            </div>
            <div class="kpi-card">
              <div class="icon-well tone-green">${ICONS.home}</div>
              <div class="kpi-body">
                <div class="kpi-label">${esc(t.tuitionShare)}</div>
                <div class="kpi-val">${Number(child.care_tuition.parent_share || 0).toLocaleString()} ${esc(t.won)}</div>
              </div>
            </div>
          </div>
        </div>`;
    }

    if (secId === "schedules") {
      return `
        <div class="card section-card ${wideClass}" data-section="schedules">
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

    if (secId === "automations") {
      return renderAutomationsSection(child, {
        ko,
        t,
        openRecipeId: this._openRecipeId,
        copiedId: this._copiedRecipeId,
        wideClass,
      });
    }
    return "";
  }

  _renderLangDropdown(t, activeLang) {
    if (!this._langMenuOpen) return "";
    const prefLang = this._prefs?.lang || "auto";
    const autoActive = prefLang === "auto";
    const items = LANGUAGES.map((l) => {
      const selected = prefLang === l.code;
      const effective = autoActive && activeLang === l.code;
      return `
        <button type="button" class="lang-option ${selected ? "active" : ""}" role="menuitemradio" aria-checked="${selected ? "true" : "false"}" data-quick-lang="${esc(l.code)}">
          <span class="lang-opt-label">${esc(l.label)}</span>
          <span class="lang-opt-right">
            <span class="lang-opt-code">${esc(l.short)}</span>
            <span class="lang-opt-check">${selected ? "&#10003;" : effective ? "&#8226;" : ""}</span>
          </span>
        </button>`;
    }).join("");
    return `
      <div class="lang-backdrop" id="lang-backdrop"></div>
      <div class="lang-dropdown" role="menu" aria-label="${esc(t.settingsLang)}">
        <button type="button" class="lang-option ${autoActive ? "active" : ""}" role="menuitemradio" aria-checked="${autoActive ? "true" : "false"}" data-quick-lang="auto">
          <span class="lang-opt-label">${esc(t.langAuto)}</span>
          <span class="lang-opt-right">
            <span class="lang-opt-code">${esc(getLangMeta(activeLang).short)}</span>
            <span class="lang-opt-check">${autoActive ? "&#10003;" : ""}</span>
          </span>
        </button>
        <div class="lang-divider"></div>
        ${items}
      </div>`;
  }

  _renderSettingsDrawer() {
    if (!this._settingsOpen) return "";
    const t = this._t();
    const ko = this._isKo();
    const p = this._settingsDraft || this._prefs;
    const isDirty = JSON.stringify(p) !== JSON.stringify(this._prefs);
    const secLabels = {
      care: t.secCare,
      timeline: t.secTimeline,
      measurements: t.secMeasurements,
      growth: t.secGrowth,
      tuition: t.secTuition,
      schedules: t.secSchedules,
      automations: t.secAutomations,
    };

    const layoutCards = LAYOUT_MODES.map(
      (lm) => `
        <button type="button" class="style-card ${p.layout === lm.id ? "active" : ""}" data-select-layout="${esc(lm.id)}">
          <div class="theme-name">${esc(ko ? lm.nameKo : lm.nameEn)}</div>
          <div class="theme-desc">${esc(ko ? lm.descKo : lm.descEn)}</div>
        </button>`
    ).join("");

    const cardStyleBtns = CARD_STYLES.map(
      (cs) => `
        <button type="button" class="style-card ${p.cardStyle === cs.id ? "active" : ""}" data-select-cardstyle="${esc(cs.id)}">
          <div class="theme-name">${esc(ko ? cs.nameKo : cs.nameEn)}</div>
          <div class="theme-desc">${esc(ko ? cs.descKo : cs.descEn)}</div>
        </button>`
    ).join("");

    const themeCards = THEMES.map((th) => {
      const active = p.theme === th.id;
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

    const canToggleWide = ["bento", "bento-3", "quad-dense"].includes(p.layout);
    const sectionRows = p.order
      .map((secId, idx) => {
        const checked = p.visible[secId] ? "checked" : "";
        const isWide = Boolean(p.wide[secId]);
        return `
          <div class="order-row">
            <label class="checkbox-label">
              <input type="checkbox" data-toggle-section="${esc(secId)}" ${checked} />
              <span>${esc(secLabels[secId] || secId)}</span>
            </label>
            <div class="order-btns">
              ${
                canToggleWide
                  ? `<button type="button" class="btn-outline small" data-toggle-wide="${esc(secId)}">${esc(isWide ? t.widthFull : t.widthHalf)}</button>`
                  : ""
              }
              <button type="button" class="btn-outline small" data-move-sec="${esc(secId)}" data-dir="-1" ${idx === 0 ? "disabled" : ""}>&#8593;</button>
              <button type="button" class="btn-outline small" data-move-sec="${esc(secId)}" data-dir="1" ${idx === p.order.length - 1 ? "disabled" : ""}>&#8595;</button>
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
              <div class="drawer-label">${esc(t.settingsLang)}</div>
              <div class="lang-grid">
                <button type="button" class="seg ${p.lang === "auto" ? "active" : ""}" data-select-lang="auto">${esc(t.langAuto)}</button>
                ${LANGUAGES.map(
                  (l) =>
                    `<button type="button" class="seg ${p.lang === l.code ? "active" : ""}" data-select-lang="${esc(l.code)}">${esc(l.label)}</button>`
                ).join("")}
              </div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsCardStyle)}</div>
              <div class="theme-grid">${cardStyleBtns}</div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsLayout)}</div>
              <div class="theme-grid">${layoutCards}</div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsMobileCols)}</div>
              <div class="seg-group">
                <button type="button" class="seg ${p.mobileCols === 2 ? "active" : ""}" data-select-mcols="2">${esc(t.mcol2)}</button>
                <button type="button" class="seg ${p.mobileCols === 3 ? "active" : ""}" data-select-mcols="3">${esc(t.mcol3)}</button>
                <button type="button" class="seg ${p.mobileCols === 4 ? "active" : ""}" data-select-mcols="4">${esc(t.mcol4)}</button>
              </div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsSections)}</div>
              <div class="order-list">
                <div class="order-row">
                  <label class="checkbox-label">
                    <input type="checkbox" data-toggle-section="chips" ${p.visible.chips ? "checked" : ""} />
                    <span>${esc(t.secChips)}</span>
                  </label>
                </div>
                ${sectionRows}
                <div class="order-row">
                  <label class="checkbox-label">
                    <input type="checkbox" data-toggle-section="footer" ${p.visible.footer ? "checked" : ""} />
                    <span>${esc(t.secFooter)}</span>
                  </label>
                </div>
              </div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsTheme)}</div>
              <div class="theme-grid">${themeCards}</div>
            </div>

            <div class="drawer-sec">
              <div class="drawer-label">${esc(t.settingsDefaultTab)}</div>
              <div class="seg-group">
                <button type="button" class="seg ${p.defaultScheduleTab === "vaccines" ? "active" : ""}" data-default-tab="vaccines">${esc(t.tabVaccines)}</button>
                <button type="button" class="seg ${p.defaultScheduleTab === "checkups" ? "active" : ""}" data-default-tab="checkups">${esc(t.tabCheckups)}</button>
                <button type="button" class="seg ${p.defaultScheduleTab === "oral" ? "active" : ""}" data-default-tab="oral">${esc(t.tabOral)}</button>
              </div>
            </div>
          </div>
          <div class="drawer-footer">
            <button type="button" class="btn-outline small" id="btn-reset-prefs">${esc(t.resetPrefs)}</button>
            <div class="right-actions">
              <button type="button" class="btn-outline" id="btn-cancel-settings">${esc(t.cancel)}</button>
              <button type="button" class="btn-primary" id="btn-save-settings">${esc(t.save)}${isDirty ? " ●" : ""}</button>
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

  _renderCareModal() {
    if (!this._careModalOpen || !this._currentChild()) return "";
    const t = this._t();
    const d = this._careDraft || this._emptyCareDraft();
    const logKinds = ["note", "feeding", "sleep", "diaper", "tummy_time", "pumping", "temperature"];
    return `
      <div class="backdrop care-modal-backdrop" id="care-backdrop">
        <div class="modal care-modal" role="dialog" aria-modal="true">
          <div class="card-head" style="margin-bottom:10px;">
            <h3>${esc(t.logDetailTitle)}</h3>
            <button type="button" class="btn-outline small" id="btn-close-care">${esc(t.close)}</button>
          </div>
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
              <textarea name="note" data-care-field="note" rows="3" placeholder="${esc(t.notePlaceholder)}">${esc(d.note)}</textarea>
            </label>
            <div class="photo-row">
              <label class="btn-outline small photo-upload-btn">
                ${ICONS.camera} <span>${esc(t.attachPhoto)}</span>
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

  _renderMobileNav() {
    const t = this._t();
    const items = [
      { id: "all", icon: ICONS.home, label: t.navAll },
      { id: "care", icon: ICONS.feeding, label: t.navCare },
      { id: "growth", icon: ICONS.ruler, label: t.navGrowth },
      { id: "diary", icon: ICONS.note, label: t.navDiary },
      { id: "schedule", icon: ICONS.vaccine, label: t.navSchedule },
      { id: "auto", icon: ICONS.bolt, label: t.navAuto },
    ];
    return `
      <nav class="mobile-nav" aria-label="Navigation">
        ${items
          .map(
            (it) => `
              <button type="button" class="mnav-btn ${this._mobileNav === it.id ? "active" : ""}" data-mobile-nav="${esc(it.id)}">
                ${it.icon}
                <span>${esc(it.label)}</span>
              </button>`
          )
          .join("")}
      </nav>`;
  }

  _mobileVisibleSections() {
    if (this._mobileNav === "care") return new Set(["care"]);
    if (this._mobileNav === "growth") return new Set(["growth", "measurements", "tuition"]);
    if (this._mobileNav === "diary") return new Set(["timeline"]);
    if (this._mobileNav === "schedule") return new Set(["schedules"]);
    if (this._mobileNav === "auto") return new Set(["automations"]);
    return null;
  }

  _sectionWeight(secId, child) {
    if (secId === "care") return 3.3;
    if (secId === "growth") {
      const pcts = child.percentiles || {};
      return pcts.height || pcts.weight || pcts.head ? 3.5 : 2.3;
    }
    if (secId === "measurements") return 1.9;
    if (secId === "timeline") {
      const n = (child.activities || []).length;
      return 1.3 + Math.min(2.2, n * 0.35);
    }
    if (secId === "schedules") return 3.1;
    if (secId === "tuition") return 1.1;
    if (secId === "automations") return 2.8;
    return 1.5;
  }

  _renderBalancedColumns(activeIds, child, colCount) {
    const blocks = [];
    let cols = Array.from({ length: colCount }, () => []);
    let weights = Array.from({ length: colCount }, () => 0);

    const flush = () => {
      const nonEmpty = cols.filter((c) => c.length > 0);
      if (!nonEmpty.length) return;
      if (nonEmpty.length === 1) {
        blocks.push(`<div class="bento-single">${nonEmpty[0].join("")}</div>`);
      } else {
        blocks.push(
          `<div class="bento-columns cols-${nonEmpty.length}">${nonEmpty
            .map((c) => `<div class="bento-col">${c.join("")}</div>`)
            .join("")}</div>`
        );
      }
      cols = Array.from({ length: colCount }, () => []);
      weights = Array.from({ length: colCount }, () => 0);
    };

    for (const secId of activeIds) {
      const rendered = this._renderSection(secId, child);
      if (!rendered) continue;
      if (this._prefs.wide[secId]) {
        flush();
        blocks.push(`<div class="bento-wide">${rendered}</div>`);
      } else {
        let minIdx = 0;
        for (let i = 1; i < colCount; i++) {
          if (weights[i] < weights[minIdx]) minIdx = i;
        }
        cols[minIdx].push(rendered);
        weights[minIdx] += this._sectionWeight(secId, child);
      }
    }
    flush();
    return blocks.join("");
  }

  _renderSectionsContainer(child) {
    const mode = this._prefs.layout;
    const layoutClass = `layout-${mode}`;
    const mFilter = this._mobileVisibleSections();
    const activeIds = this._prefs.order.filter((secId) => !mFilter || mFilter.has(secId));
    const isNarrowViewport =
      this._narrow || Boolean(window.matchMedia?.("(max-width: 920px)")?.matches);

    if (mode === "app-tabs") {
      const t = this._t();
      const deckTabs = [
        { id: "care", label: t.navCare, secs: ["care"] },
        { id: "growth", label: t.navGrowth, secs: ["growth", "measurements", "tuition"] },
        { id: "diary", label: t.navDiary, secs: ["timeline"] },
        { id: "schedule", label: t.navSchedule, secs: ["schedules"] },
        { id: "auto", label: t.navAuto, secs: ["automations"] },
      ];
      const cur = deckTabs.find((d) => d.id === this._appDeckTab) || deckTabs[0];
      const deckNav = `<div class="app-deck-bar">${deckTabs
        .map(
          (d) =>
            `<button type="button" class="pill ${cur.id === d.id ? "active" : ""}" data-deck-tab="${esc(d.id)}">${esc(d.label)}</button>`
        )
        .join("")}</div>`;
      const html = cur.secs.map((secId) => this._renderSection(secId, child)).join("");
      return `${deckNav}<div class="sections-wrap layout-app-tabs">${html}</div>`;
    }

    if (isNarrowViewport || mode === "single" || mode === "compact") {
      const html = activeIds.map((secId) => this._renderSection(secId, child)).join("");
      return `<div class="sections-wrap ${layoutClass}">${html}</div>`;
    }

    if (mode === "bento-3") {
      return `<div class="sections-wrap layout-bento-3">${this._renderBalancedColumns(activeIds, child, 3)}</div>`;
    }

    if (mode === "cockpit") {
      const topHtml = activeIds.includes("care") ? this._renderSection("care", child) : "";
      const restIds = activeIds.filter((id) => id !== "care");
      const mainIds = restIds.filter((id) => id === "growth" || id === "timeline" || id === "automations");
      const sideIds = restIds.filter((id) => !mainIds.includes(id));
      return `
        <div class="sections-wrap layout-cockpit">
          ${topHtml ? `<div class="bento-wide">${topHtml}</div>` : ""}
          <div class="cockpit-split">
            <div class="bento-col">${mainIds.map((id) => this._renderSection(id, child)).join("")}</div>
            <div class="bento-col">${sideIds.map((id) => this._renderSection(id, child)).join("")}</div>
          </div>
        </div>`;
    }

    if (mode === "magazine") {
      const dockSet = new Set(["care", "measurements", "tuition"]);
      const dockHtml = activeIds
        .filter((id) => dockSet.has(id))
        .map((id) => this._renderSection(id, child))
        .join("");
      const streamHtml = activeIds
        .filter((id) => !dockSet.has(id))
        .map((id) => this._renderSection(id, child))
        .join("");
      return `
        <div class="sections-wrap layout-magazine">
          <div class="magazine-dock bento-col">${dockHtml}</div>
          <div class="magazine-stream bento-col">${streamHtml}</div>
        </div>`;
    }

    // "bento" and "quad-dense" both use balanced 2-column cards on desktop
    // ("quad-dense" additionally packs internal tiles into 4-column micro-grids).
    return `<div class="sections-wrap ${layoutClass}">${this._renderBalancedColumns(activeIds, child, 2)}</div>`;
  }

  _render() {
    const t = this._t();
    const children = this._data?.children || [];
    const child = this._currentChild();
    const themeStyle = getThemeCss(this._prefs.theme);
    const cStyle = cardStyleCss(this._prefs.cardStyle);

    let bodyHtml = "";
    if (!child) {
      bodyHtml = `<div class="card"><p class="muted">${esc(t.noChildren)}</p></div>`;
    } else {
      const sexLabel = child.sex === "male" ? t.male : t.female;
      const initial = (child.name || "?").trim().slice(0, 1).toUpperCase();
      const livedDays = daysBetween(child.birthdate, child.today);
      const sectionsContainerHtml = this._renderSectionsContainer(child);

      bodyHtml = `
        <div class="hero-card card">
          <div class="hero-top">
            <div class="child-id-wrap">
              <label class="avatar-btn" title="${esc(t.changePhoto)}">
                ${
                  child.avatar_url
                    ? `<img src="${esc(child.avatar_url)}" class="avatar-img" alt="${esc(child.name)}" />`
                    : `<span class="avatar-fallback">${esc(initial)}</span>`
                }
                <span class="avatar-cam">${ICONS.camera}</span>
                <input type="file" id="avatar-input" accept="image/*" hidden />
              </label>
              <div>
                <div class="hero-name-row">
                  <h2>${esc(child.name)}</h2>
                  ${livedDays != null && livedDays >= 0 ? `<span class="day-pill">${esc(t.daysOld(livedDays + 1))}</span>` : ""}
                </div>
                <div class="meta">
                  <span>${esc(t.ageMonths(child.age_months))}</span>
                  <span>·</span>
                  <span>${esc(child.birthdate)}</span>
                  <span>·</span>
                  <span>${esc(sexLabel)}</span>
                </div>
              </div>
            </div>
            <button class="btn-outline small" id="btn-edit-child">${esc(t.editChild)}</button>
          </div>
          ${this._renderStatusChips(child)}
        </div>

        ${sectionsContainerHtml}

        ${
          this._prefs.visible.footer
            ? `<p class="disclaimer">${esc(this._isKo() ? (child.disclaimer_ko || child.disclaimer || "") : (child.disclaimer_en || child.disclaimer || ""))}<br/>${esc(this._isKo() ? (child.attribution_ko || child.attribution || "") : (child.attribution_en || child.attribution || ""))}</p>`
            : ""
        }
      `;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ${themeStyle}
        :host {
          display: block; min-height: 100vh;
          background-color: var(--bk-bg); background-image: var(--bk-bg-image, none);
          background-size: var(--bk-bg-size, auto); color: var(--bk-text);
          font-family: var(--bk-font-body);
          line-height: 1.45;
          word-break: keep-all;
          overflow-wrap: break-word;
          -webkit-font-smoothing: antialiased;
          text-rendering: optimizeLegibility;
          transition: background-color 0.2s ease, color 0.2s ease;
        }
        * { box-sizing: border-box; }
        .topbar {
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          padding: 12px 20px; background: var(--bk-header-bg); color: var(--bk-header-text);
          border-bottom: var(--bk-header-border); position: sticky; top: 0; z-index: 5;
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
        .topbar h1 { margin: 0; font-size: 19px; font-weight: 700; letter-spacing: -0.025em; font-family: var(--bk-font-head); }
        .lang-menu-wrap { position: relative; display: inline-flex; align-items: center; }
        .lang-btn {
          display: inline-flex; align-items: center; gap: 5px;
          font-weight: 600; white-space: nowrap;
        }
        .lang-caret { font-size: 10px; opacity: 0.78; margin-left: 1px; }
        .lang-backdrop {
          position: fixed; inset: 0; z-index: 19; background: transparent;
        }
        .lang-dropdown {
          position: absolute; top: calc(100% + 8px); right: 0; z-index: 20;
          min-width: 196px; padding: 6px;
          border-radius: 14px;
          background: var(--bk-card); color: var(--bk-text);
          border: var(--bk-card-border);
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
          backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
          display: flex; flex-direction: column; gap: 2px;
        }
        .lang-option {
          display: flex; align-items: center; justify-content: space-between; gap: 10px;
          width: 100%; padding: 8px 10px; border-radius: 9px; border: none;
          background: transparent; color: var(--bk-text); cursor: pointer;
          font-size: 13.5px; font-weight: 500; font-family: inherit; text-align: left;
          transition: background-color 0.12s ease;
        }
        .lang-option:hover { background: var(--bk-surface); }
        .lang-option.active {
          background: rgba(56, 189, 248, 0.14); color: var(--bk-accent); font-weight: 700;
        }
        .lang-opt-right { display: inline-flex; align-items: center; gap: 6px; }
        .lang-opt-code {
          font-size: 10.5px; font-weight: 700; padding: 2px 6px; border-radius: 6px;
          background: var(--bk-surface); color: var(--bk-muted);
          font-family: var(--bk-font-num);
        }
        .lang-option.active .lang-opt-code {
          background: var(--bk-accent); color: var(--bk-accent-text);
        }
        .lang-opt-check { width: 14px; text-align: center; font-size: 13px; color: var(--bk-accent); }
        .lang-divider { height: 1px; background: rgba(128, 128, 128, 0.16); margin: 4px 6px; }
        .lang-grid {
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px;
        }
        .lang-grid .seg { padding: 7px 6px; font-size: 12.5px; }
        .container {
          max-width: ${
            this._prefs.layout === "bento-3"
              ? "1740px"
              : ["bento", "quad-dense", "cockpit", "magazine"].includes(this._prefs.layout)
              ? "1440px"
              : this._prefs.layout === "app-tabs"
              ? "1020px"
              : "880px"
          };
          margin: 0 auto;
          padding: ${this._prefs.layout === "compact" || this._prefs.layout === "quad-dense" ? "12px 14px" : "18px 22px"};
        }
        .hero-card {
          margin-bottom: 16px !important;
          background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.35), rgba(107, 142, 120, 0.06));
        }
        .hero-top {
          display: flex; align-items: center; justify-content: space-between;
          gap: 12px; flex-wrap: nowrap;
        }
        .child-id-wrap { display: flex; align-items: center; gap: 14px; min-width: 0; flex: 1; }
        #btn-edit-child { flex-shrink: 0; white-space: nowrap; }
        .hero-name-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .hero-name-row h2 { margin: 0; }
        .day-pill {
          padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
          background: var(--bk-accent); color: var(--bk-accent-text);
          font-family: var(--bk-font-num);
        }
        .hero-card .chips-bar {
          margin-top: 14px; margin-bottom: 0; padding-top: 12px;
          border-top: 1px solid rgba(128, 128, 128, 0.14);
        }
        .expand-btn { align-self: center; margin-top: 6px; }
        .child-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .pill {
          padding: 7px 14px; border-radius: var(--bk-pill-radius); border: var(--bk-card-border);
          background: var(--bk-card); color: var(--bk-text); cursor: pointer; font-size: 14px;
        }
        .pill.active { background: var(--bk-accent); color: var(--bk-accent-text); border-color: transparent; }
        .chips-bar {
          display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;
        }
        .chip {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 6px 12px; border-radius: 16px; font-size: 13px; font-weight: 500;
          border: 1px solid transparent;
        }
        .tone-indigo { background: rgba(99, 102, 241, 0.14); color: #4f46e5; }
        .tone-sky { background: rgba(14, 165, 233, 0.14); color: #0284c7; }
        .tone-blue { background: rgba(59, 130, 246, 0.14); color: #2563eb; }
        .tone-teal { background: rgba(20, 184, 166, 0.15); color: #0f766e; }
        .tone-green { background: rgba(34, 197, 94, 0.15); color: #15803d; }
        .tone-amber { background: rgba(245, 158, 11, 0.17); color: #b45309; }
        .tone-rose { background: rgba(244, 63, 94, 0.15); color: #be123c; }
        .icon-well {
          width: 36px; height: 36px; border-radius: 12px; flex-shrink: 0;
          display: inline-flex; align-items: center; justify-content: center;
        }
        .sections-wrap.layout-bento,
        .sections-wrap.layout-bento-3,
        .sections-wrap.layout-quad-dense,
        .sections-wrap.layout-cockpit,
        .sections-wrap.layout-app-tabs {
          display: flex; flex-direction: column; gap: 18px;
        }
        .bento-columns {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px; align-items: start;
        }
        .bento-columns.cols-3 {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .cockpit-split {
          display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 0.9fr);
          gap: 18px; align-items: start;
        }
        .sections-wrap.layout-magazine {
          display: grid; grid-template-columns: 390px minmax(0, 1fr);
          gap: 20px; align-items: start;
        }
        .magazine-dock { position: sticky; top: 68px; }
        .app-deck-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .bento-col, .bento-single, .bento-wide {
          display: flex; flex-direction: column; gap: 18px; min-width: 0;
        }
        /* 4-Col Dense Matrix layout styling (desktop & mobile) */
        .sections-wrap.layout-quad-dense .kpi-grid {
          grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px;
        }
        .sections-wrap.layout-quad-dense .kpi-card {
          flex-direction: column; align-items: center; text-align: center;
          padding: 10px 6px !important; gap: 6px; border-radius: 14px !important;
        }
        .sections-wrap.layout-quad-dense .kpi-card .icon-well { width: 30px !important; height: 30px !important; }
        .sections-wrap.layout-quad-dense .kpi-label { font-size: 11px; }
        .sections-wrap.layout-quad-dense .kpi-val { font-size: 13.5px; }
        .sections-wrap.layout-quad-dense .timer-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
        .sections-wrap.layout-quad-dense .gauge-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
        @media (max-width: 1180px) { .bento-columns.cols-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        @media (max-width: 920px) {
          .bento-columns, .bento-columns.cols-3, .cockpit-split, .sections-wrap.layout-magazine {
            grid-template-columns: 1fr;
          }
          .magazine-dock { position: static; }
        }
        .card {
          background: var(--bk-card); backdrop-filter: var(--bk-card-backdrop);
          -webkit-backdrop-filter: var(--bk-card-backdrop);
          border-radius: var(--bk-card-radius);
          padding: ${this._prefs.layout === "compact" || this._prefs.layout === "quad-dense" ? "14px 15px" : "20px 22px"};
          margin-bottom: ${["single", "compact"].includes(this._prefs.layout) ? (this._prefs.layout === "compact" ? "10px" : "16px") : "0"};
          box-shadow: var(--bk-card-shadow); border: var(--bk-card-border);
        }
        .child-header {
          display: flex; align-items: center; justify-content: space-between;
          gap: 12px; flex-wrap: wrap; margin-bottom: 14px;
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
        h2 { margin: 0; font-size: 21px; font-weight: 700; letter-spacing: -0.025em; line-height: 1.25; font-family: var(--bk-font-head); }
        h3 { margin: 0 0 14px; font-size: 16.5px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.35; font-family: var(--bk-font-head); }
        .meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 4px; color: var(--bk-muted); font-size: 13.5px; line-height: 1.4; }
        .sub-badge {
          display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px;
          font-size: 12px; font-weight: 600; line-height: 1.2;
          background: var(--bk-surface); color: var(--bk-muted);
          border: 1px solid rgba(128, 128, 128, 0.14);
        }
        .quick-bar { display: flex; flex-wrap: wrap; gap: 6px; }
        .quick-pill {
          padding: 5px 11px; border-radius: 999px; font-size: 12px; font-weight: 600;
          background: var(--bk-surface); color: var(--bk-text);
          border: 1px solid var(--bk-input-border); cursor: pointer;
        }
        .quick-pill:hover { border-color: var(--bk-accent); color: var(--bk-accent); }
        .quick-pill.active-pill { background: var(--bk-accent); color: var(--bk-accent-text); border-color: transparent; }
        .curve-tabs { display: flex; gap: 6px; }
        .care-launcher-box {
          padding: 12px 14px; border-radius: 18px; background: var(--bk-surface);
          border: 1px solid rgba(128, 128, 128, 0.14); display: flex; flex-direction: column; gap: 10px;
        }
        .care-launcher-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
        .launcher-title { font-size: 13.5px; font-weight: 700; letter-spacing: -0.01em; color: var(--bk-text); }
        .launcher-sub { font-size: 12px; color: var(--bk-muted); line-height: 1.35; }
        .weekly-title { font-size: 12.5px; font-weight: 600; color: var(--bk-muted); }
        .care-launcher-grid {
          display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 8px;
        }
        .care-launch-btn {
          display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
          padding: 10px 6px; border-radius: 16px; border: 1px solid rgba(128, 128, 128, 0.15);
          background: var(--bk-card); color: var(--bk-text); cursor: pointer;
          font-size: 12px; font-weight: 600; font-family: inherit; transition: transform 0.12s ease, border-color 0.12s ease;
        }
        .care-launch-btn:hover { border-color: var(--bk-accent); transform: translateY(-1px); }
        .care-modal {
          max-width: 520px; background: var(--bk-card); color: var(--bk-text);
          border: var(--bk-card-border); border-radius: var(--bk-card-radius);
          font-family: var(--bk-font-body);
        }
        .curve-chart-box, .weekly-chart-box {
          padding: 12px 14px; border-radius: 18px; background: var(--bk-surface);
          border: 1px solid rgba(128, 128, 128, 0.12);
        }
        .weekly-chart-box { margin-top: 12px; }
        .weekly-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }
        .curve-svg { width: 100%; height: auto; max-height: 225px; display: block; }
        .weekly-svg { width: 100%; height: auto; max-height: 130px; display: block; }
        .curve-legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: var(--bk-muted); margin-top: 4px; }
        .curve-legend span { display: inline-flex; align-items: center; gap: 5px; }
        .lg-band { width: 12px; height: 8px; border-radius: 3px; background: var(--bk-accent); opacity: 0.25; display: inline-block; }
        .lg-mid { width: 12px; height: 2px; background: var(--bk-accent); opacity: 0.7; display: inline-block; }
        .lg-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--bk-accent); display: inline-block; }
        .lg-sleep { width: 9px; height: 9px; border-radius: 3px; background: #6366f1; display: inline-block; }
        .lg-feed { width: 9px; height: 9px; border-radius: 3px; background: #0ea5e9; display: inline-block; }
        .kpi-grid {
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px; margin-bottom: 14px;
        }
        .tuition-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
          margin-bottom: 0;
        }
        .kpi-card {
          display: flex; align-items: center; gap: 12px;
          padding: 13px 15px; border-radius: 18px;
          background: var(--bk-surface); border: 1px solid rgba(128, 128, 128, 0.12);
          min-width: 0;
        }
        .kpi-body {
          display: flex; flex-direction: column; gap: 3px; min-width: 0;
        }
        .kpi-label {
          font-size: 12.5px; font-weight: 500; color: var(--bk-muted);
          line-height: 1.3; margin: 0; padding: 0;
        }
        .kpi-ago { color: var(--bk-accent); font-weight: 600; font-variant-numeric: tabular-nums; }
        /* Smart Nursery Automation Recipe cards */
        .auto-list { display: flex; flex-direction: column; gap: 10px; margin-top: 4px; }
        .bento-wide .auto-list, .sections-wrap.layout-cockpit .auto-list {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;
        }
        .bento-wide .auto-card.open, .sections-wrap.layout-cockpit .auto-card.open {
          grid-column: 1 / -1;
        }
        .auto-card {
          padding: 14px 16px; border-radius: 18px; background: var(--bk-surface);
          border: 1px solid rgba(128, 128, 128, 0.14); display: flex; flex-direction: column; gap: 8px;
        }
        .auto-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
        .auto-meta { display: flex; flex-direction: column; align-items: flex-start; gap: 5px; min-width: 0; flex: 1; }
        .auto-title { font-size: 14.5px; font-weight: 700; line-height: 1.35; color: var(--bk-text); }
        .auto-why { margin: 0; font-size: 13px; color: var(--bk-muted); line-height: 1.5; }
        .auto-devs { display: flex; flex-wrap: wrap; gap: 6px; }
        .auto-dev-pill {
          font-size: 11.5px; font-weight: 500; padding: 3px 9px; border-radius: 999px;
          background: var(--bk-card); color: var(--bk-muted); border: 1px solid rgba(128, 128, 128, 0.16);
        }
        .auto-yaml-wrap {
          margin-top: 4px; border-radius: 12px; overflow: hidden;
          border: 1px solid rgba(128, 128, 128, 0.2); background: #141821; color: #e2e8f0;
        }
        .auto-yaml-bar {
          display: flex; align-items: center; justify-content: space-between;
          padding: 8px 12px; background: rgba(255, 255, 255, 0.06);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .auto-yaml-bar code { color: #7dd3fc; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        .auto-pre {
          margin: 0; padding: 12px 14px; overflow-x: auto; font-size: 12px; line-height: 1.5;
          font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        }
        .kpi-val {
          font-size: 17px; font-weight: 700; color: var(--bk-text);
          font-family: var(--bk-font-num); font-variant-numeric: tabular-nums;
          letter-spacing: -0.02em; line-height: 1.25; margin: 0; padding: 0;
        }
        .timer-grid {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
          gap: 10px; margin-bottom: 14px;
        }
        .timer-tile {
          padding: 10px 14px; border-radius: 18px;
          background: var(--bk-surface); border: 1px solid rgba(128, 128, 128, 0.15);
          display: flex; align-items: center; justify-content: space-between; gap: 10px;
        }
        .timer-tile.running { border-color: var(--bk-accent); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.22); }
        .timer-left { display: flex; align-items: center; gap: 10px; }
        .timer-name { font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
        .timer-clock { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 15px; font-weight: 700; color: var(--bk-accent); }
        .timer-btns { display: flex; align-items: center; gap: 6px; }
        .sub-btn {
          width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--bk-input-border);
          background: var(--bk-card); color: var(--bk-text); cursor: pointer;
          display: inline-flex; align-items: center; justify-content: center;
        }
        .sub-btn.primary { background: var(--bk-accent); color: var(--bk-accent-text); border-color: transparent; }
        .pulse-dot {
          width: 8px; height: 8px; border-radius: 50%; background: #ef4444;
          display: inline-block; animation: bk-pulse 1.2s infinite;
        }
        @keyframes bk-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }
        .gauge-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
        .kpi-val { white-space: nowrap; }
        .gauge-card {
          padding: 14px 16px; border-radius: 18px; background: var(--bk-surface);
          border: 1px solid rgba(128, 128, 128, 0.12);
          display: flex; flex-direction: column; gap: 9px;
        }
        .gauge-top { display: flex; align-items: center; gap: 11px; }
        .gauge-meta { flex: 1; }
        .gauge-summary { font-size: 12.5px; color: var(--bk-muted); line-height: 1.45; margin: 0; padding: 0; }
        .pct-gauge { display: flex; flex-direction: column; gap: 4px; }
        .pct-track { position: relative; height: 8px; border-radius: 999px; background: rgba(128, 128, 128, 0.16); overflow: visible; }
        .pct-safe { position: absolute; left: 5%; right: 5%; top: 0; bottom: 0; background: rgba(34, 197, 94, 0.16); border-radius: 999px; }
        .pct-mid { position: absolute; left: 50%; top: -2px; bottom: -2px; width: 1.5px; background: rgba(128, 128, 128, 0.45); }
        .pct-fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; opacity: 0.35; }
        .pct-dot { position: absolute; top: 50%; width: 14px; height: 14px; border-radius: 50%; transform: translate(-50%, -50%); border: 2px solid var(--bk-card); box-shadow: 0 1px 4px rgba(0,0,0,0.25); }
        .pct-axis { display: flex; justify-content: space-between; font-size: 10px; color: var(--bk-muted); }
        .spark-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-top: 12px; }
        .spark-wrap { padding: 10px 12px; border-radius: 14px; background: var(--bk-surface); }
        .spark-svg { width: 100%; height: 48px; display: block; }
        .spark-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--bk-muted); margin-top: 4px; font-family: var(--bk-font-num); }
        .photo-strip { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px; margin-bottom: 10px; }
        .strip-thumb { width: 72px; height: 72px; border-radius: 12px; object-fit: cover; cursor: zoom-in; flex-shrink: 0; border: 1px solid var(--bk-input-border); }
        .care-form { display: flex; flex-direction: column; gap: 10px; }
        .photo-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .photo-upload-btn { display: inline-flex; flex-direction: row; align-items: center; gap: 6px; cursor: pointer; }
        .photo-preview-wrap { display: flex; align-items: center; gap: 8px; }
        .photo-preview { width: 52px; height: 52px; object-fit: cover; border-radius: 8px; border: 1px solid var(--bk-input-border); }
        .tl-list { display: flex; flex-direction: column; gap: 10px; }
        .tl-item {
          display: flex; align-items: flex-start; gap: 12px;
          padding: 11px 14px; border-radius: 16px; background: var(--bk-surface);
        }
        .tl-body { display: flex; flex-direction: column; gap: 6px; flex: 1; }
        .tl-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .tl-time { font-size: 12px; color: var(--bk-muted); font-variant-numeric: tabular-nums; }
        .tl-note { font-size: 14px; white-space: pre-wrap; line-height: 1.45; }
        .tl-photo { max-width: 240px; max-height: 180px; border-radius: 12px; object-fit: cover; cursor: zoom-in; border: 1px solid var(--bk-input-border); }
        .lightbox-img { max-width: 92vw; max-height: 90vh; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,0.5); }
        .grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
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
        .small { font-size: 12.5px; line-height: 1.4; }
        button.small, .btn-outline.small, .btn-primary.small, label.small {
          font-size: 12.5px; font-weight: 600; padding: 6px 12px; line-height: 1.2;
        }
        .muted { color: var(--bk-muted); }
        .badge {
          display: inline-flex; align-items: center; padding: 3px 9px;
          border-radius: var(--bk-pill-radius); font-size: 11.5px; font-weight: 600;
          line-height: 1.2; font-variant-numeric: tabular-nums;
        }
        .badge.neutral { background: rgba(128, 128, 128, 0.16); }
        .badge.ok, .badge.status-done { background: rgba(76, 175, 80, 0.18); color: #2e7d32; }
        .badge.warn, .badge.status-open { background: rgba(255, 152, 0, 0.22); color: #d97706; }
        .badge.status-upcoming { background: rgba(3, 169, 244, 0.18); color: var(--bk-accent); }
        .badge.status-past { background: rgba(128, 128, 128, 0.16); color: var(--bk-muted); }
        .card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
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
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          padding: 12px 15px; border-radius: 18px; background: var(--bk-surface);
          border: 1px solid rgba(128, 128, 128, 0.1);
        }
        .sched-left { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
        .sched-meta { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
        .sched-title { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; font-size: 14.5px; line-height: 1.35; }
        .sched-date { font-size: 12.5px; color: var(--bk-muted); line-height: 1.35; font-variant-numeric: tabular-nums; }
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
        .theme-card, .style-card {
          text-align: left; padding: 9px; border-radius: 10px; border: 1.5px solid var(--divider-color, #ddd);
          background: var(--primary-background-color, #fafafa); color: var(--primary-text-color, #212121);
          cursor: pointer; display: flex; flex-direction: column; gap: 5px;
        }
        .theme-card.active, .style-card.active { border-color: var(--primary-color, #03a9f4); box-shadow: 0 0 0 2px rgba(3, 169, 244, 0.22); }
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
        .drawer-footer {
          padding: 14px 20px max(14px, env(safe-area-inset-bottom));
          border-top: 1px solid var(--divider-color, #e0e0e0);
          background: var(--card-background-color, #ffffff);
          display: flex; align-items: center; justify-content: space-between; gap: 10px;
          flex-shrink: 0;
        }
        .modal {
          background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
          border-radius: 12px; padding: 20px; width: 100%; max-width: 420px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25); font-family: system-ui, -apple-system, sans-serif;
        }
        .modal form { display: flex; flex-direction: column; gap: 12px; }
        .modal-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
        .right-actions { display: flex; gap: 8px; }
        .mobile-nav { display: none; }
        @media (max-width: 720px) {
          .topbar {
            padding: max(10px, env(safe-area-inset-top)) 12px 10px;
          }
          .topbar h1 { font-size: 18px; }
          .btn-top { padding: 7px 11px; font-size: 13px; }
          .container { padding: 12px 10px calc(86px + env(safe-area-inset-bottom)); }
          .child-header { padding: 14px; }
          .avatar-btn { width: 54px; height: 54px; }
          .child-pills, .chips-bar, .quick-bar, .tabs {
            flex-wrap: nowrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            padding-bottom: 4px;
          }
          .child-pills::-webkit-scrollbar,
          .chips-bar::-webkit-scrollbar,
          .quick-bar::-webkit-scrollbar,
          .tabs::-webkit-scrollbar { display: none; }
          .pill, .chip, .quick-pill, .tab { flex-shrink: 0; white-space: nowrap; }
          .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
          .tuition-grid { grid-template-columns: 1fr; }
          .timer-grid { grid-template-columns: 1fr; }
          .gauge-grid, .spark-grid, .grid-2, .grid-3 { grid-template-columns: 1fr; }
          /* Mobile 3-col & 4-col ultra-dense tile overrides */
          .bento-wide .auto-list, .sections-wrap.layout-cockpit .auto-list {
            grid-template-columns: 1fr;
          }
          .mcols-3 .kpi-grid, .mcols-3 .tuition-grid, .mcols-4 .tuition-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important; gap: 6px !important;
          }
          .mcols-4 .kpi-grid, .sections-wrap.layout-quad-dense .kpi-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important; gap: 6px !important;
          }
          .mcols-3 .kpi-card, .mcols-4 .kpi-card {
            flex-direction: column !important; align-items: center !important; text-align: center !important;
            padding: 9px 5px !important; gap: 5px !important; border-radius: 14px !important;
          }
          .mcols-3 .kpi-card .icon-well, .mcols-4 .kpi-card .icon-well {
            width: 28px !important; height: 28px !important;
          }
          .mcols-3 .kpi-label, .mcols-4 .kpi-label { font-size: 10.5px !important; line-height: 1.2 !important; }
          .mcols-3 .kpi-ago, .mcols-4 .kpi-ago { display: none; }
          .mcols-3 .kpi-val, .mcols-4 .kpi-val { font-size: 12px !important; white-space: normal !important; }
          .mcols-3 .timer-grid, .mcols-4 .timer-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 6px !important;
          }
          .mcols-4 .timer-tile { padding: 8px 10px !important; }
          .mcols-4 .timer-clock { font-size: 13px !important; }
          input, select, textarea { font-size: 16px; min-height: 44px; }
          .btn-primary, .btn-outline, .quick-pill { min-height: 40px; }
          .sub-btn { width: 40px; height: 40px; }
          .tl-photo { max-width: 100%; max-height: 220px; }
          .drawer { max-width: 100vw; }
          .care-modal-backdrop { align-items: flex-end; padding: 0; }
          .care-modal {
            max-width: 100vw; border-bottom-left-radius: 0; border-bottom-right-radius: 0;
            padding: 18px 16px calc(20px + env(safe-area-inset-bottom));
          }
          .care-launcher-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
          .theme-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
          .mobile-nav {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            position: fixed;
            left: 0; right: 0; bottom: 0;
            z-index: 30;
            background: var(--bk-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-top: var(--bk-card-border);
            padding: 6px 4px max(6px, env(safe-area-inset-bottom));
            box-shadow: 0 -4px 18px rgba(0, 0, 0, 0.08);
          }
          .mnav-btn {
            background: transparent;
            border: none;
            color: var(--bk-muted);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            padding: 6px 2px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 12px;
            font-family: inherit;
          }
          .mnav-btn.active {
            color: var(--bk-accent);
            font-weight: 700;
          }
        }
        ${cStyle}
      </style>

      <div class="topbar">
        <div class="topbar-left">
          <button class="menu-btn" id="btn-menu" aria-label="Menu">&#9776;</button>
          <h1>${esc(t.title)}</h1>
        </div>
        <div class="topbar-right">
          <div class="lang-menu-wrap">
            <button type="button" class="btn-top lang-btn" id="btn-lang-menu" aria-haspopup="menu" aria-expanded="${this._langMenuOpen ? "true" : "false"}" title="${esc(t.settingsLang)}">
              ${ICONS.globe}<span>${esc(getLangMeta(this._lang()).short)}</span><span class="lang-caret">&#9662;</span>
            </button>
            ${this._renderLangDropdown(t, this._lang())}
          </div>
          <button class="btn-top" id="btn-add-child">+ ${esc(t.addChild)}</button>
          <button class="icon-btn" id="btn-open-settings" title="${esc(t.settingsTitle)}" aria-label="${esc(t.settingsTitle)}">${ICONS.gear}</button>
        </div>
      </div>

      <div class="container mcols-${esc(this._prefs.mobileCols || 2)}">
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

      ${child ? this._renderMobileNav() : ""}
      ${this._renderCareModal()}
      ${this._renderModal()}
      ${this._renderSettingsDrawer()}
      ${this._renderLightbox()}
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-mobile-nav]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._mobileNav = btn.getAttribute("data-mobile-nav");
        this._render();
        window.scrollTo?.({ top: 0, behavior: "smooth" });
      });
    });
    root.getElementById("btn-lang-menu")?.addEventListener("click", () => {
      this._langMenuOpen = !this._langMenuOpen;
      this._render();
    });
    root.getElementById("lang-backdrop")?.addEventListener("click", () => {
      this._langMenuOpen = false;
      this._render();
    });
    root.querySelectorAll("[data-quick-lang]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const nextLang = btn.getAttribute("data-quick-lang");
        this._langMenuOpen = false;
        this._updatePrefs((p) => { p.lang = nextLang; });
      });
    });
    root.querySelectorAll("[data-select-lang]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const lang = btn.getAttribute("data-select-lang");
        this._updateSettingsDraft((p) => { p.lang = lang; });
      });
    });
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
    root.querySelectorAll("[data-quick-log]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-quick-log");
        if (mode === "wet") this._quickLog("diaper", { diaper_type: "wet" });
        else if (mode === "solid") this._quickLog("diaper", { diaper_type: "solid" });
        else if (mode === "feed140") this._quickLog("feeding", { method: "formula", amount_ml: 140 });
        else if (mode === "tummy10") this._quickLog("tummy_time", { duration_min: 10 });
      });
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
    root.querySelectorAll("[data-open-care]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._careKind = btn.getAttribute("data-open-care");
        this._careModalOpen = true;
        this._error = null;
        this._render();
      });
    });
    root.getElementById("btn-close-care")?.addEventListener("click", () => {
      this._careModalOpen = false;
      this._render();
    });
    root.getElementById("care-backdrop")?.addEventListener("click", (e) => {
      if (e.target.id === "care-backdrop") {
        this._careModalOpen = false;
        this._render();
      }
    });
    root.querySelectorAll("[data-care-kind]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._careKind = btn.getAttribute("data-care-kind");
        this._render();
      });
    });
    root.querySelectorAll("[data-care-field]").forEach((el) => {
      const update = () => {
        const key = el.getAttribute("data-care-field");
        if (key) this._careDraft[key] = el.value;
      };
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });
    root.querySelectorAll("[data-measure-field]").forEach((el) => {
      const update = () => {
        const child = this._currentChild();
        const key = el.getAttribute("data-measure-field");
        if (child && key) {
          this._measureDraft[child.child_id] = this._measureDraft[child.child_id] || {};
          this._measureDraft[child.child_id][key] = el.value;
        }
      };
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });
    root.querySelectorAll("[data-curve-kind]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._growthChartKind = btn.getAttribute("data-curve-kind");
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
      this._settingsDraft = structuredClone(this._prefs);
      this._settingsOpen = true;
      this._render();
    });
    const closeSettings = () => {
      this._settingsOpen = false;
      this._settingsDraft = null;
      this._render();
    };
    root.getElementById("btn-close-settings")?.addEventListener("click", closeSettings);
    root.getElementById("btn-cancel-settings")?.addEventListener("click", closeSettings);
    root.getElementById("settings-backdrop")?.addEventListener("click", (e) => {
      if (e.target.id === "settings-backdrop") closeSettings();
    });
    root.getElementById("btn-save-settings")?.addEventListener("click", () => {
      if (this._settingsDraft) {
        this._prefs = structuredClone(this._settingsDraft);
        this._scheduleTab = this._prefs.defaultScheduleTab;
        savePrefs(this._prefs);
      }
      this._settingsOpen = false;
      this._settingsDraft = null;
      this._flash(this._t().saved);
    });
    root.querySelectorAll("[data-select-cardstyle]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-select-cardstyle");
        this._updateSettingsDraft((p) => { p.cardStyle = id; });
      });
    });
    root.querySelectorAll("[data-select-theme]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-select-theme");
        this._updateSettingsDraft((p) => { p.theme = id; });
      });
    });
    root.querySelectorAll("[data-select-layout]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-select-layout");
        this._updateSettingsDraft((p) => { p.layout = mode; });
      });
    });
    root.querySelectorAll("[data-select-mcols]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const cols = Number(btn.getAttribute("data-select-mcols")) || 2;
        this._updateSettingsDraft((p) => { p.mobileCols = cols; });
      });
    });
    root.querySelectorAll("[data-deck-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._appDeckTab = btn.getAttribute("data-deck-tab");
        this._render();
      });
    });
    root.querySelectorAll("[data-toggle-recipe]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const rid = btn.getAttribute("data-toggle-recipe");
        this._openRecipeId = this._openRecipeId === rid ? null : rid;
        this._render();
      });
    });
    root.querySelectorAll("[data-copy-recipe]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const rid = btn.getAttribute("data-copy-recipe");
        const recipe = AUTOMATION_RECIPES.find((r) => r.id === rid);
        const cid = this._currentChild()?.child_id || "your_child_id";
        if (!recipe) return;
        try {
          await navigator.clipboard?.writeText(recipe.yaml(cid, this._isKo()));
          this._copiedRecipeId = rid;
          this._render();
          setTimeout(() => {
            if (this._copiedRecipeId === rid) {
              this._copiedRecipeId = null;
              this._render();
            }
          }, 1800);
        } catch {
          // Ignore clipboard permission errors in insecure contexts.
        }
      });
    });
    root.querySelectorAll("[data-toggle-section]").forEach((chk) => {
      chk.addEventListener("change", () => {
        const sec = chk.getAttribute("data-toggle-section");
        this._updateSettingsDraft((p) => { p.visible[sec] = chk.checked; });
      });
    });
    root.querySelectorAll("[data-toggle-wide]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sec = btn.getAttribute("data-toggle-wide");
        this._updateSettingsDraft((p) => { p.wide[sec] = !p.wide[sec]; });
      });
    });
    root.querySelectorAll("[data-move-sec]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sec = btn.getAttribute("data-move-sec");
        const dir = Number(btn.getAttribute("data-dir"));
        this._updateSettingsDraft((p) => {
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
        this._updateSettingsDraft((p) => { p.defaultScheduleTab = tab; });
      });
    });
    root.getElementById("btn-reset-prefs")?.addEventListener("click", () => {
      this._settingsDraft = structuredClone(DEFAULT_PREFS);
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
        this._careDraft = this._emptyCareDraft();
        this._careModalOpen = false;
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
    root.getElementById("btn-expand-sched")?.addEventListener("click", () => {
      this._expandSchedule = !this._expandSchedule;
      this._render();
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
