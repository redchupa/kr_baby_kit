/* Visual card primitives for Baby Kit:
 * - Crisp SVG icon set (no cheesy emojis)
 * - 0-100% LMS percentile bar with 5-95% normal band & marker
 * - Smooth SVG growth sparkline for height/weight history
 * - Card-style CSS presets: bubble | mushroom | bento-pro | classic
 */

export const ICONS = {
  gear: `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
  camera: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>`,
  sleep: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
  feeding: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4"/><path d="M9 6h6"/><path d="M8 9h8l1 11a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L8 9z"/><path d="M9 14h6"/></svg>`,
  diaper: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
  tummy_time: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  pumping: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12"/><path d="M12 2v6"/><rect x="7" y="8" width="10" height="13" rx="3"/></svg>`,
  temperature: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>`,
  note: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  ruler: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.3 8.7 8.7 21.3c-1 1-2.5 1-3.4 0l-2.6-2.6c-1-1-1-2.5 0-3.4L15.3 2.7c1-1 2.5-1 3.4 0l2.6 2.6c1 1 1 2.5 0 3.4Z"/><path d="m7.5 10.5 2 2"/><path d="m10.5 7.5 2 2"/><path d="m13.5 4.5 2 2"/><path d="m4.5 13.5 2 2"/></svg>`,
  scale: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 16h3a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h3"/><circle cx="12" cy="11" r="3"/><path d="M12 11l1.5-1.5"/></svg>`,
  vaccine: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3c-1 1-2.5 1-3.4 0l-.6-.6c-1-1-1-2.5 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/><path d="m14 4 6 6"/></svg>`,
  checkup: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  shield: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  play: `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"/></svg>`,
  stop: `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`,
  home: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  wallet: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>`,
};

export const CARD_STYLES = [
  { id: "bubble", nameKo: "버블 카드", nameEn: "Bubble Card", descKo: "캡슐형 필 카드와 원형 아이콘·서브 버튼", descEn: "Pill capsules with circular icon wells & sub-buttons" },
  { id: "mushroom", nameKo: "템플릿 카드", nameEn: "Template Card", descKo: "머쉬룸 스타일 아이콘 배지·칩 요약", descEn: "Mushroom-style icon badges & status chips" },
  { id: "bento-pro", nameKo: "벤토 프로", nameEn: "Bento Pro", descKo: "대형 수치 KPI와 게이지·스파크라인 강조", descEn: "Large KPI typography & visual gauges" },
  { id: "classic", nameKo: "클래식", nameEn: "Classic", descKo: "단정하고 익숙한 표준 카드", descEn: "Clean standard Home Assistant cards" },
];

export function cardStyleCss(styleId) {
  if (styleId === "bubble") {
    return `
      .card {
        border-radius: 26px !important;
      }
      .kpi-card, .timer-tile, .sched-item, .tl-item, .gauge-card {
        border-radius: 20px !important;
        padding: 13px 16px !important;
      }
      .icon-well {
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
      }
      .chip {
        border-radius: 999px !important;
        padding: 7px 14px !important;
      }
      .btn-primary, .btn-outline, .btn-top, .tab, .pill, .sub-badge {
        border-radius: 999px !important;
      }
      @media (max-width: 720px) {
        .card { border-radius: 22px !important; }
        .kpi-card, .timer-tile, .sched-item, .tl-item, .gauge-card {
          border-radius: 18px !important;
          padding: 12px 14px !important;
        }
      }
    `;
  }
  if (styleId === "mushroom") {
    return `
      .kpi-card {
        border-radius: 14px !important;
        padding: 12px 14px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
      }
      .icon-well {
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
      }
      .chip {
        border-radius: 14px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      }
      .timer-tile {
        border-radius: 16px !important;
      }
    `;
  }
  if (styleId === "bento-pro") {
    return `
      .kpi-card {
        border-radius: 18px !important;
        padding: 16px !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 10px !important;
      }
      .kpi-val {
        font-size: 24px !important;
        letter-spacing: -0.02em;
      }
      .icon-well {
        border-radius: 12px !important;
        width: 36px !important;
        height: 36px !important;
      }
      .chip {
        border-radius: 10px !important;
        font-weight: 600;
      }
    `;
  }
  return "";
}

export function renderPercentileGauge(pct, { warnBand = false } = {}) {
  if (pct == null || Number.isNaN(Number(pct))) return "";
  const clamped = Math.max(1, Math.min(99, Number(pct)));
  const isWarn = warnBand && (clamped < 5 || clamped > 95);
  const dotColor = isWarn ? "#e11d48" : "var(--bk-accent)";
  return `
    <div class="pct-gauge" aria-label="${clamped.toFixed(1)}%">
      <div class="pct-track">
        <div class="pct-safe"></div>
        <div class="pct-mid"></div>
        <div class="pct-fill" style="width:${clamped}%;background:${dotColor};"></div>
        <div class="pct-dot" style="left:${clamped}%;background:${dotColor};"></div>
      </div>
      <div class="pct-axis">
        <span>0%</span><span>50%</span><span>100%</span>
      </div>
    </div>`;
}

export function renderSparkline(records, field, unit) {
  const pts = (records || [])
    .filter((r) => r && r[field] != null)
    .slice(-12)
    .map((r) => ({ d: r.date, v: Number(r[field]) }));
  if (pts.length < 2) return "";
  const w = 220;
  const h = 48;
  const pad = 6;
  const vals = pts.map((p) => p.v);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const coords = pts.map((p, i) => {
    const x = pad + (i / (pts.length - 1)) * (w - pad * 2);
    const y = h - pad - ((p.v - min) / span) * (h - pad * 2);
    return [x, y];
  });
  const poly = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${coords[0][0].toFixed(1)},${h - pad} ${poly} ${coords[coords.length - 1][0].toFixed(1)},${h - pad}`;
  const last = coords[coords.length - 1];
  const delta = (pts[pts.length - 1].v - pts[0].v).toFixed(1);
  const sign = Number(delta) >= 0 ? "+" : "";
  return `
    <div class="spark-wrap">
      <svg viewBox="0 0 ${w} ${h}" class="spark-svg" preserveAspectRatio="none">
        <polygon points="${area}" fill="var(--bk-accent)" fill-opacity="0.14" />
        <polyline points="${poly}" fill="none" stroke="var(--bk-accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="3.5" fill="var(--bk-accent)" />
      </svg>
      <div class="spark-meta">
        <span>${pts[0].d.slice(5)} (${pts[0].v}${unit})</span>
        <span>${sign}${delta}${unit}</span>
        <span>${pts[pts.length - 1].d.slice(5)} (${pts[pts.length - 1].v}${unit})</span>
      </div>
    </div>`;
}
