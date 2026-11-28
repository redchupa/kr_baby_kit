/* SVG visualization components for Baby Kit:
 * 1. Interactive LMS Growth Curve Chart (P3/P15/P50/P85/P97 bands + child dots + current-age guide)
 * 2. 7-Day Sleep & Feeding Care Trend Bar Chart (Baby Buddy-style)
 */

function esc(val) {
  return String(val ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function renderGrowthCurveChart(curveData, currentAgeMonths, opts = {}) {
  const bands = curveData?.bands || [];
  const points = curveData?.points || [];
  if (bands.length < 2) return "";

  const unit = opts.unit || "cm";
  const ko = Boolean(opts.ko);
  const t = opts.t || null;
  const monthSuffix = t?.chartMonthsSuffix ?? (ko ? "개월" : "m");
  const lblRefBand = t?.chartRefBand ?? (ko ? "정상 범위 (3-97%)" : "Reference band (3-97%)");
  const lblMedian = t?.chartMedian ?? (ko ? "50% 평균선" : "50% median");
  const lblRecorded = t?.chartRecorded ?? (ko ? "우리 아이 기록" : "Recorded");
  const W = 460;
  const H = 205;
  const padL = 38;
  const padR = 34;
  const padT = 14;
  const padB = 26;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const minX = bands[0].age_months;
  const maxX = bands[bands.length - 1].age_months || 24;
  const spanX = Math.max(1, maxX - minX);

  let minY = Math.min(...bands.map((b) => b.p3));
  let maxY = Math.max(...bands.map((b) => b.p97));
  for (const pt of points) {
    if (pt.age_months <= maxX + 0.5) {
      minY = Math.min(minY, pt.value);
      maxY = Math.max(maxY, pt.value);
    }
  }
  const padY = (maxY - minY) * 0.08 || 1;
  minY = Math.max(0, minY - padY);
  maxY = maxY + padY;
  const spanY = Math.max(0.1, maxY - minY);

  const sx = (age) => padL + ((age - minX) / spanX) * plotW;
  const sy = (val) => padT + plotH - ((val - minY) / spanY) * plotH;

  const polyBand = (loKey, hiKey) => {
    const upper = bands.map((b) => `${sx(b.age_months).toFixed(1)},${sy(b[hiKey]).toFixed(1)}`);
    const lower = [...bands]
      .reverse()
      .map((b) => `${sx(b.age_months).toFixed(1)},${sy(b[loKey]).toFixed(1)}`);
    return [...upper, ...lower].join(" ");
  };

  const p50Line = bands
    .map((b) => `${sx(b.age_months).toFixed(1)},${sy(b.p50).toFixed(1)}`)
    .join(" ");
  const p97Line = bands
    .map((b) => `${sx(b.age_months).toFixed(1)},${sy(b.p97).toFixed(1)}`)
    .join(" ");
  const p3Line = bands
    .map((b) => `${sx(b.age_months).toFixed(1)},${sy(b.p3).toFixed(1)}`)
    .join(" ");

  const yTicks = [0, 0.33, 0.67, 1].map((t) => minY + spanY * t);
  const yGridSvg = yTicks
    .map((v) => {
      const y = sy(v).toFixed(1);
      const lbl = unit === "kg" ? v.toFixed(1) : Math.round(v);
      return `
        <line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="currentColor" stroke-opacity="0.08" stroke-width="1" />
        <text x="${padL - 6}" y="${Number(y) + 3.5}" text-anchor="end" font-size="9.5" fill="var(--bk-muted)">${lbl}</text>`;
    })
    .join("");

  const stepM = maxX <= 24 ? 6 : maxX <= 60 ? 12 : 24;
  const xTicks = [];
  for (let m = 0; m <= maxX; m += stepM) xTicks.push(m);
  if (xTicks[xTicks.length - 1] < maxX - stepM * 0.4) xTicks.push(Math.round(maxX));
  const xGridSvg = xTicks
    .map((m) => {
      const x = sx(m).toFixed(1);
      return `<text x="${x}" y="${H - 7}" text-anchor="middle" font-size="9.5" fill="var(--bk-muted)">${m}${esc(monthSuffix)}</text>`;
    })
    .join("");

  const lastBand = bands[bands.length - 1];
  const bandLabels = [
    { key: "p97", text: "97%" },
    { key: "p50", text: "50%" },
    { key: "p3", text: "3%" },
  ]
    .map(
      (b) =>
        `<text x="${W - padR + 4}" y="${(sy(lastBand[b.key]) + 3).toFixed(1)}" font-size="9" fill="var(--bk-muted)">${b.text}</text>`
    )
    .join("");

  let ageGuideSvg = "";
  if (currentAgeMonths != null && currentAgeMonths >= minX && currentAgeMonths <= maxX) {
    const ax = sx(currentAgeMonths).toFixed(1);
    ageGuideSvg = `
      <line x1="${ax}" y1="${padT}" x2="${ax}" y2="${padT + plotH}" stroke="var(--bk-accent)" stroke-opacity="0.35" stroke-width="1.2" stroke-dasharray="3 3" />`;
  }

  const visiblePts = points.filter((p) => p.age_months >= minX && p.age_months <= maxX + 0.5);
  let childSvg = "";
  if (visiblePts.length > 0) {
    const childLine =
      visiblePts.length > 1
        ? `<polyline points="${visiblePts
            .map((p) => `${sx(p.age_months).toFixed(1)},${sy(p.value).toFixed(1)}`)
            .join(" ")}" fill="none" stroke="var(--bk-accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />`
        : "";
    const dots = visiblePts
      .map((p, idx) => {
        const cx = sx(p.age_months).toFixed(1);
        const cy = sy(p.value).toFixed(1);
        const isLast = idx === visiblePts.length - 1;
        return `
          <circle cx="${cx}" cy="${cy}" r="${isLast ? 4.8 : 3.4}" fill="var(--bk-accent)" stroke="var(--bk-card)" stroke-width="1.8">
            <title>${esc(p.date)}: ${p.value} ${esc(unit)}</title>
          </circle>
          ${
            isLast
              ? `<text x="${cx}" y="${Math.max(padT + 10, Number(cy) - 8).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="700" fill="var(--bk-text)">${p.value}${esc(unit)}</text>`
              : ""
          }`;
      })
      .join("");
    childSvg = childLine + dots;
  }

  return `
    <div class="curve-chart-box">
      <svg viewBox="0 0 ${W} ${H}" class="curve-svg" role="img" aria-label="LMS growth curve">
        ${yGridSvg}
        <polygon points="${polyBand("p3", "p97")}" fill="var(--bk-accent)" fill-opacity="0.09" />
        <polygon points="${polyBand("p15", "p85")}" fill="var(--bk-accent)" fill-opacity="0.16" />
        <polyline points="${p97Line}" fill="none" stroke="var(--bk-accent)" stroke-opacity="0.28" stroke-width="1" />
        <polyline points="${p3Line}" fill="none" stroke="var(--bk-accent)" stroke-opacity="0.28" stroke-width="1" />
        <polyline points="${p50Line}" fill="none" stroke="var(--bk-accent)" stroke-opacity="0.55" stroke-width="1.4" stroke-dasharray="4 3" />
        ${ageGuideSvg}
        ${childSvg}
        ${bandLabels}
        ${xGridSvg}
      </svg>
      <div class="curve-legend">
        <span><i class="lg-band"></i>${esc(lblRefBand)}</span>
        <span><i class="lg-mid"></i>${esc(lblMedian)}</span>
        <span><i class="lg-dot"></i>${esc(lblRecorded)}</span>
      </div>
    </div>`;
}

export function renderWeeklyCareChart(weeklyCare, opts = {}) {
  const days = weeklyCare || [];
  if (!days.length) return "";
  const anyData = days.some(
    (d) => (d.sleep_min || 0) > 0 || (d.feeding_ml || 0) > 0 || (d.diaper_count || 0) > 0
  );
  if (!anyData) return "";

  const ko = Boolean(opts.ko);
  const t = opts.t || null;
  const lblLast7 = t?.chartLast7Days ?? (ko ? "최근 7일 돌봄 추이" : "Last 7 days");
  const lblSleep = t?.chartSleep ?? (ko ? "수면" : "Sleep");
  const lblFeed = t?.chartFeedMl ?? (ko ? "수유량(ml)" : "Feeding(ml)");
  const W = 440;
  const H = 118;
  const padL = 12;
  const padR = 12;
  const padT = 18;
  const padB = 22;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const maxSleep = Math.max(60, ...days.map((d) => Number(d.sleep_min || 0)));
  const maxFeed = Math.max(150, ...days.map((d) => Number(d.feeding_ml || 0)));
  const slotW = plotW / days.length;

  const barsSvg = days
    .map((d, idx) => {
      const cx = padL + slotW * (idx + 0.5);
      const sH = Math.max(2, (Number(d.sleep_min || 0) / maxSleep) * plotH);
      const fH = Math.max(2, (Number(d.feeding_ml || 0) / maxFeed) * plotH);
      const bw = Math.min(13, slotW * 0.28);
      const sY = padT + plotH - sH;
      const fY = padT + plotH - fH;
      const mmdd = String(d.date || "").slice(5).replace("-", "/");
      const sleepHours = (Number(d.sleep_min || 0) / 60).toFixed(1);
      return `
        <g>
          <rect x="${(cx - bw - 1.5).toFixed(1)}" y="${sY.toFixed(1)}" width="${bw.toFixed(1)}" height="${sH.toFixed(1)}" rx="4" fill="#6366f1" fill-opacity="0.82">
            <title>${esc(d.date)} ${esc(lblSleep)}: ${sleepHours}h</title>
          </rect>
          <rect x="${(cx + 1.5).toFixed(1)}" y="${fY.toFixed(1)}" width="${bw.toFixed(1)}" height="${fH.toFixed(1)}" rx="4" fill="#0ea5e9" fill-opacity="0.82">
            <title>${esc(d.date)} ${esc(lblFeed)}: ${d.feeding_ml || 0}ml</title>
          </rect>
          <text x="${cx.toFixed(1)}" y="${H - 6}" text-anchor="middle" font-size="9.5" fill="var(--bk-muted)">${esc(mmdd)}</text>
        </g>`;
    })
    .join("");

  return `
    <div class="weekly-chart-box">
      <div class="weekly-head">
        <span class="weekly-title">${esc(lblLast7)}</span>
        <div class="curve-legend">
          <span><i class="lg-sleep"></i>${esc(lblSleep)}</span>
          <span><i class="lg-feed"></i>${esc(lblFeed)}</span>
        </div>
      </div>
      <svg viewBox="0 0 ${W} ${H}" class="weekly-svg" role="img" aria-label="7-day care chart">
        <line x1="${padL}" y1="${padT + plotH}" x2="${W - padR}" y2="${padT + plotH}" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
        ${barsSvg}
      </svg>
    </div>`;
}
