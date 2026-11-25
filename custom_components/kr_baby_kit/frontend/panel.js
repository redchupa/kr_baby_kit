/* Home Assistant Sidebar Panel for Korean Baby Kit (kr_baby_kit) */

const STRINGS = {
  ko: {
    title: "영유아 키트",
    addChild: "아이 추가",
    editChild: "정보 수정",
    deleteChild: "삭제",
    deleteConfirm: "이 아이와 저장된 측정 기록·완료 표시를 모두 삭제할까요?",
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
    saving: "저장 중...",
    saved: "저장되었습니다.",
    ageMonths: (m) => `생후 ${m}개월`,
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
  },
  en: {
    title: "Baby Kit",
    addChild: "Add child",
    editChild: "Edit info",
    deleteChild: "Delete",
    deleteConfirm: "Delete this child along with all stored measurements and completion marks?",
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
    saving: "Saving...",
    saved: "Saved.",
    ageMonths: (m) => `${m} mo`,
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
  },
};

function esc(val) {
  return String(val ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

class KrBabyKitPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._data = null;
    this._selectedId = null;
    this._scheduleTab = "vaccines";
    this._showPast = false;
    this._modal = null; // null | { mode: "add" | "edit", child?: object }
    this._busy = false;
    this._notice = null;
    this._error = null;
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

  _render() {
    const t = this._t();
    const ko = this._isKo();
    const children = this._data?.children || [];
    const child = this._currentChild();

    let bodyHtml = "";
    if (!child) {
      bodyHtml = `<div class="card"><p class="muted">${esc(t.noChildren)}</p></div>`;
    } else {
      const pcts = child.percentiles || {};
      const hInfo = pcts.height;
      const wInfo = pcts.weight;
      const headInfo = pcts.head;
      const bmiInfo = pcts.bmi;
      const wfl = child.weight_for_length;
      const sumKey = ko ? "summary_ko" : "summary_en";
      const sexLabel = child.sex === "male" ? t.male : t.female;
      const profLabel = child.profile === "kr" ? "KR · KDCA" : "WHO";

      const tuitionHtml =
        child.profile === "kr" && child.care_tuition
          ? `
            <div class="card">
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
            </div>`
          : "";

      bodyHtml = `
        <div class="card child-header">
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
          <button class="btn-outline" id="btn-edit-child">${esc(t.editChild)}</button>
        </div>

        <div class="card">
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
        </div>

        <div class="card">
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
        </div>

        ${tuitionHtml}

        <div class="card">
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
        </div>

        <p class="disclaimer">${esc(child.disclaimer || "")}<br/>${esc(child.attribution || "")}</p>
      `;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          background: var(--primary-background-color, #fafafa);
          color: var(--primary-text-color, #212121);
          font-family: var(--paper-font-body1_-_font-family, system-ui, -apple-system, sans-serif);
        }
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 12px 20px;
          background: var(--app-header-background-color, var(--primary-color, #03a9f4));
          color: var(--app-header-text-color, #fff);
          position: sticky;
          top: 0;
          z-index: 5;
        }
        .topbar-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .menu-btn {
          background: transparent;
          border: none;
          color: inherit;
          font-size: 22px;
          cursor: pointer;
          padding: 4px 8px;
          display: ${this._narrow ? "inline-flex" : "none"};
        }
        .topbar h1 {
          margin: 0;
          font-size: 20px;
          font-weight: 500;
        }
        .container {
          max-width: 960px;
          margin: 0 auto;
          padding: 16px;
        }
        .child-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 16px;
        }
        .pill {
          padding: 8px 14px;
          border-radius: 18px;
          border: 1px solid var(--divider-color, #ddd);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #212121);
          cursor: pointer;
          font-size: 14px;
        }
        .pill.active {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          border-color: transparent;
        }
        .card {
          background: var(--card-background-color, #fff);
          border-radius: 12px;
          padding: 16px 20px;
          margin-bottom: 16px;
          box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0, 0, 0, 0.08));
          border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
        }
        .child-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          flex-wrap: wrap;
        }
        h2 { margin: 0 0 6px; font-size: 20px; font-weight: 600; }
        h3 { margin: 0 0 12px; font-size: 16px; font-weight: 600; }
        .meta {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
          color: var(--secondary-text-color, #666);
          font-size: 14px;
        }
        .grid-3 {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 12px;
        }
        .grid-4 {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 12px;
        }
        label {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 13px;
          color: var(--secondary-text-color, #555);
        }
        input, select {
          padding: 9px 10px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #ccc);
          background: var(--primary-background-color, #fafafa);
          color: var(--primary-text-color, #212121);
          font-size: 14px;
        }
        .hint { font-size: 12px; color: var(--secondary-text-color, #777); }
        .form-footer {
          display: flex;
          justify-content: flex-end;
          margin-top: 12px;
        }
        .btn-primary, .btn-outline, .btn-danger, .btn-top {
          padding: 8px 14px;
          border-radius: 8px;
          font-size: 14px;
          cursor: pointer;
          border: 1px solid transparent;
        }
        .btn-primary {
          background: var(--primary-color, #03a9f4);
          color: #fff;
        }
        .btn-top {
          background: rgba(255, 255, 255, 0.18);
          color: #fff;
          border-color: rgba(255, 255, 255, 0.35);
        }
        .btn-outline {
          background: transparent;
          color: var(--primary-text-color, #212121);
          border-color: var(--divider-color, #ccc);
        }
        .btn-danger {
          background: transparent;
          color: var(--error-color, #db4437);
          border-color: var(--error-color, #db4437);
        }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .small { font-size: 12px; padding: 5px 10px; }
        .muted { color: var(--secondary-text-color, #666); }
        .stat {
          padding: 10px 12px;
          border-radius: 8px;
          background: var(--primary-background-color, #f5f5f5);
        }
        .stat-val { font-size: 18px; font-weight: 600; margin: 4px 0; }
        .concerns {
          margin-top: 12px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .concern-row {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }
        .concern-label { font-weight: 500; min-width: 110px; }
        .badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
          font-weight: 500;
        }
        .badge.neutral { background: rgba(128, 128, 128, 0.15); }
        .badge.ok, .badge.status-done { background: rgba(76, 175, 80, 0.18); color: var(--success-color, #2e7d32); }
        .badge.warn, .badge.status-open { background: rgba(255, 152, 0, 0.2); color: var(--warning-color, #e65100); }
        .badge.status-upcoming { background: rgba(3, 169, 244, 0.16); color: var(--primary-color, #0277bd); }
        .badge.status-past { background: rgba(128, 128, 128, 0.16); color: var(--secondary-text-color, #666); }
        .card-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 10px;
        }
        .card-head h3 { margin: 0; }
        .checkbox-label {
          flex-direction: row;
          align-items: center;
          gap: 6px;
          cursor: pointer;
        }
        .tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
          padding-bottom: 8px;
        }
        .tab {
          background: transparent;
          border: none;
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          color: var(--secondary-text-color, #666);
          font-size: 14px;
        }
        .tab.active {
          background: var(--primary-color, #03a9f4);
          color: #fff;
        }
        .sched-list { display: flex; flex-direction: column; gap: 8px; }
        .sched-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 10px 12px;
          border-radius: 8px;
          background: var(--primary-background-color, #f5f5f5);
        }
        .sched-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .banner {
          padding: 10px 14px;
          border-radius: 8px;
          margin-bottom: 12px;
          font-size: 14px;
        }
        .banner.error { background: rgba(219, 68, 55, 0.15); color: var(--error-color, #c62828); }
        .banner.notice { background: rgba(76, 175, 80, 0.15); color: var(--success-color, #2e7d32); }
        .disclaimer {
          font-size: 12px;
          color: var(--secondary-text-color, #777);
          text-align: center;
          margin: 16px 0 32px;
          line-height: 1.5;
        }
        .backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 50;
          padding: 16px;
        }
        .modal {
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #212121);
          border-radius: 12px;
          padding: 20px;
          width: 100%;
          max-width: 420px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        }
        .modal form { display: flex; flex-direction: column; gap: 12px; }
        .modal-actions {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-top: 8px;
        }
        .right-actions { display: flex; gap: 8px; }
      </style>

      <div class="topbar">
        <div class="topbar-left">
          <button class="menu-btn" id="btn-menu" aria-label="Menu">&#9776;</button>
          <h1>${esc(t.title)}</h1>
        </div>
        <button class="btn-top" id="btn-add-child">+ ${esc(t.addChild)}</button>
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
