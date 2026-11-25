/* 12 distinct architectural themes for the Baby Kit sidebar panel.
 * Each theme defines not just palette, but also typography, card geometry,
 * surface elevation, background texture, header style, and badge treatment.
 */

export const THEMES = [
  {
    id: "ha-native",
    nameKo: "HA 기본",
    nameEn: "HA Native",
    descKo: "Home Assistant 기본 테마와 자동 동기화",
    descEn: "Matches your Home Assistant theme",
    swatch: { bg: "#fafafa", card: "#ffffff", accent: "#03a9f4", border: "#e0e0e0", radius: "12px" },
    css: `
      :host {
        --bk-bg: var(--primary-background-color, #fafafa);
        --bk-bg-image: none;
        --bk-card: var(--card-background-color, #ffffff);
        --bk-card-border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
        --bk-card-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0, 0, 0, 0.08));
        --bk-card-radius: 12px;
        --bk-card-backdrop: none;
        --bk-text: var(--primary-text-color, #212121);
        --bk-muted: var(--secondary-text-color, #666666);
        --bk-accent: var(--primary-color, #03a9f4);
        --bk-accent-text: #ffffff;
        --bk-surface: var(--primary-background-color, #f5f5f5);
        --bk-header-bg: var(--app-header-background-color, var(--primary-color, #03a9f4));
        --bk-header-text: var(--app-header-text-color, #ffffff);
        --bk-header-border: none;
        --bk-font-body: var(--paper-font-body1_-_font-family, system-ui, -apple-system, sans-serif);
        --bk-font-head: inherit;
        --bk-font-num: inherit;
        --bk-btn-radius: 8px;
        --bk-pill-radius: 18px;
        --bk-input-bg: var(--primary-background-color, #fafafa);
        --bk-input-border: var(--divider-color, #cccccc);
      }
    `,
  },
  {
    id: "nordic-nursery",
    nameKo: "노르딕 육아실",
    nameEn: "Nordic Nursery",
    descKo: "따뜻한 오트밀 배경, 둥근 카드, 세리프 제목",
    descEn: "Warm linen, plush rounded cards, serif titles",
    swatch: { bg: "#f6f2ea", card: "#fffdf9", accent: "#6b8e78", border: "#e7dfd3", radius: "22px" },
    css: `
      :host {
        --bk-bg: #f6f2ea;
        --bk-bg-image: radial-gradient(circle at 15% 10%, #fdfaf3 0%, transparent 45%), radial-gradient(circle at 85% 90%, #ebe4d6 0%, transparent 50%);
        --bk-card: #fffdf9;
        --bk-card-border: 1px solid #e7dfd3;
        --bk-card-shadow: 0 10px 28px rgba(107, 94, 75, 0.07);
        --bk-card-radius: 22px;
        --bk-card-backdrop: none;
        --bk-text: #3a342c;
        --bk-muted: #7c7265;
        --bk-accent: #6b8e78;
        --bk-accent-text: #ffffff;
        --bk-surface: #f4efe6;
        --bk-header-bg: #fffdf9;
        --bk-header-text: #3a342c;
        --bk-header-border: 1px solid #e7dfd3;
        --bk-font-body: "Pretendard", "Nunito", system-ui, -apple-system, sans-serif;
        --bk-font-head: Georgia, "Times New Roman", serif;
        --bk-font-num: inherit;
        --bk-btn-radius: 14px;
        --bk-pill-radius: 999px;
        --bk-input-bg: #f9f6f0;
        --bk-input-border: #dfd6c7;
      }
      .btn-top { background: #6b8e78 !important; color: #fff !important; border-color: transparent !important; }
      .stat { border-radius: 16px !important; }
    `,
  },
  {
    id: "paper-journal",
    nameKo: "육아 일기장",
    nameEn: "Paper Journal",
    descKo: "도트 노트 질감, 얇은 잉크 테두리, 에디토리얼",
    descEn: "Dot-grid stationery, crisp ink rules, editorial",
    swatch: { bg: "#faf6ee", card: "#fffef9", accent: "#2c4a3e", border: "#cfc5b4", radius: "4px" },
    css: `
      :host {
        --bk-bg: #faf6ee;
        --bk-bg-image: radial-gradient(#d7cdbc 1px, transparent 1px);
        --bk-bg-size: 20px 20px;
        --bk-card: #fffef9;
        --bk-card-border: 1px solid #cfc5b4;
        --bk-card-shadow: 0 2px 0 #e5dccb;
        --bk-card-radius: 4px;
        --bk-card-backdrop: none;
        --bk-text: #24211c;
        --bk-muted: #6e6559;
        --bk-accent: #2c4a3e;
        --bk-accent-text: #faf6ee;
        --bk-surface: #f6f0e4;
        --bk-header-bg: #fffef9;
        --bk-header-text: #24211c;
        --bk-header-border: 2px double #b8ab96;
        --bk-font-body: Georgia, "Noto Serif KR", serif;
        --bk-font-head: Georgia, "Noto Serif KR", serif;
        --bk-font-num: ui-monospace, SFMono-Regular, Menlo, monospace;
        --bk-btn-radius: 3px;
        --bk-pill-radius: 3px;
        --bk-input-bg: #fffdf8;
        --bk-input-border: #c5baa8;
      }
      .btn-top { background: #2c4a3e !important; color: #faf6ee !important; border-color: #2c4a3e !important; }
      .tabs { border-bottom-style: dashed !important; }
      .sched-item { border: 1px dashed #d8cebd; }
    `,
  },
  {
    id: "glass-aurora",
    nameKo: "오로라 글래스",
    nameEn: "Aurora Glass",
    descKo: "반투명 블러 글래스 카드와 파스텔 오로라 배경",
    descEn: "Frosted translucent glass over soft aurora mesh",
    swatch: { bg: "#dfe9ff", card: "rgba(255,255,255,0.72)", accent: "#5b6cff", border: "#ffffff", radius: "20px" },
    css: `
      :host {
        --bk-bg: #e8efff;
        --bk-bg-image: radial-gradient(at 10% 15%, #ffd6e8 0px, transparent 50%),
                       radial-gradient(at 85% 20%, #c4f0ff 0px, transparent 50%),
                       radial-gradient(at 60% 85%, #dcd3ff 0px, transparent 55%);
        --bk-card: rgba(255, 255, 255, 0.68);
        --bk-card-border: 1px solid rgba(255, 255, 255, 0.85);
        --bk-card-shadow: 0 12px 32px rgba(91, 108, 255, 0.12);
        --bk-card-radius: 20px;
        --bk-card-backdrop: blur(16px);
        --bk-text: #1e2438;
        --bk-muted: #556080;
        --bk-accent: #5b6cff;
        --bk-accent-text: #ffffff;
        --bk-surface: rgba(255, 255, 255, 0.55);
        --bk-header-bg: rgba(255, 255, 255, 0.65);
        --bk-header-text: #1e2438;
        --bk-header-border: 1px solid rgba(255, 255, 255, 0.8);
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: inherit;
        --bk-font-num: inherit;
        --bk-btn-radius: 12px;
        --bk-pill-radius: 999px;
        --bk-input-bg: rgba(255, 255, 255, 0.8);
        --bk-input-border: rgba(91, 108, 255, 0.25);
      }
      .topbar { backdrop-filter: blur(16px); }
      .btn-top { background: #5b6cff !important; color: #fff !important; border-color: transparent !important; }
    `,
  },
  {
    id: "midnight-studio",
    nameKo: "미드나잇 스튜디오",
    nameEn: "Midnight Studio",
    descKo: "딥 슬레이트 다크 모드, 선명한 시안 수치 표시",
    descEn: "Deep slate dark mode with crisp cyan numeric readouts",
    swatch: { bg: "#0f141e", card: "#171f2e", accent: "#38bdf8", border: "#263248", radius: "14px" },
    css: `
      :host {
        --bk-bg: #0f141e;
        --bk-bg-image: radial-gradient(circle at 80% 0%, rgba(56, 189, 248, 0.12), transparent 45%);
        --bk-card: #171f2e;
        --bk-card-border: 1px solid #263248;
        --bk-card-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        --bk-card-radius: 14px;
        --bk-card-backdrop: none;
        --bk-text: #e6edf7;
        --bk-muted: #8fa1bc;
        --bk-accent: #38bdf8;
        --bk-accent-text: #07131e;
        --bk-surface: #111824;
        --bk-header-bg: #131a27;
        --bk-header-text: #e6edf7;
        --bk-header-border: 1px solid #263248;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: inherit;
        --bk-font-num: ui-monospace, SFMono-Regular, Menlo, monospace;
        --bk-btn-radius: 10px;
        --bk-pill-radius: 12px;
        --bk-input-bg: #0f1520;
        --bk-input-border: #2c3a54;
      }
      .btn-top { background: #38bdf8 !important; color: #07131e !important; font-weight: 600; }
      .stat-val { color: #7dd3fc; }
    `,
  },
  {
    id: "bento-pop",
    nameKo: "벤토 팝",
    nameEn: "Bento Pop",
    descKo: "굵은 외곽선과 입체 그림자, 경쾌한 네오 브루탈리즘",
    descEn: "Bold outlines, crisp offset shadows, playful tactile feel",
    swatch: { bg: "#fff8e7", card: "#ffffff", accent: "#ff6b4a", border: "#1f1f1f", radius: "14px" },
    css: `
      :host {
        --bk-bg: #fff8e7;
        --bk-bg-image: none;
        --bk-card: #ffffff;
        --bk-card-border: 2px solid #1f1f1f;
        --bk-card-shadow: 4px 4px 0 #1f1f1f;
        --bk-card-radius: 14px;
        --bk-card-backdrop: none;
        --bk-text: #1f1f1f;
        --bk-muted: #57534e;
        --bk-accent: #ff6b4a;
        --bk-accent-text: #ffffff;
        --bk-surface: #fef0d1;
        --bk-header-bg: #ffd166;
        --bk-header-text: #1f1f1f;
        --bk-header-border: 2px solid #1f1f1f;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: system-ui, -apple-system, sans-serif;
        --bk-font-num: inherit;
        --bk-btn-radius: 10px;
        --bk-pill-radius: 10px;
        --bk-input-bg: #fffdf7;
        --bk-input-border: #1f1f1f;
      }
      .btn-top, .btn-primary, .btn-outline, .pill { border: 2px solid #1f1f1f !important; box-shadow: 2px 2px 0 #1f1f1f; font-weight: 600; }
      .btn-top { background: #ff6b4a !important; color: #fff !important; }
      .stat { border: 2px solid #1f1f1f; }
    `,
  },
  {
    id: "clinical-chart",
    nameKo: "소아과 차트",
    nameEn: "Pediatric Chart",
    descKo: "좌측 상태 바, 고밀도 정밀 그리드, 의료 기록 스타일",
    descEn: "Left accent rails, structured medical-record precision",
    swatch: { bg: "#f1f5f9", card: "#ffffff", accent: "#0f766e", border: "#cbd5e1", radius: "6px" },
    css: `
      :host {
        --bk-bg: #f1f5f9;
        --bk-bg-image: none;
        --bk-card: #ffffff;
        --bk-card-border: 1px solid #cbd5e1;
        --bk-card-shadow: none;
        --bk-card-radius: 6px;
        --bk-card-backdrop: none;
        --bk-text: #0f172a;
        --bk-muted: #475569;
        --bk-accent: #0f766e;
        --bk-accent-text: #ffffff;
        --bk-surface: #f8fafc;
        --bk-header-bg: #0f172a;
        --bk-header-text: #f8fafc;
        --bk-header-border: 3px solid #0f766e;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: inherit;
        --bk-font-num: ui-monospace, SFMono-Regular, Menlo, monospace;
        --bk-btn-radius: 4px;
        --bk-pill-radius: 4px;
        --bk-input-bg: #ffffff;
        --bk-input-border: #94a3b8;
      }
      .card { border-left: 4px solid #0f766e !important; }
      .stat { border: 1px solid #e2e8f0; }
      h3 { text-transform: uppercase; letter-spacing: 0.04em; font-size: 13px !important; color: #0f766e; }
    `,
  },
  {
    id: "botanical-linen",
    nameKo: "보태니컬 리넨",
    nameEn: "Botanical Linen",
    descKo: "유칼립투스 그린과 부드러운 패브릭 질감",
    descEn: "Eucalyptus green, soft woven linen, organic calm",
    swatch: { bg: "#eef2ec", card: "#fbfcfa", accent: "#3f6a54", border: "#d3dfd0", radius: "18px" },
    css: `
      :host {
        --bk-bg: #eef2ec;
        --bk-bg-image: repeating-linear-gradient(45deg, rgba(63, 106, 84, 0.025) 0px, rgba(63, 106, 84, 0.025) 2px, transparent 2px, transparent 10px);
        --bk-card: #fbfcfa;
        --bk-card-border: 1px solid #d3dfd0;
        --bk-card-shadow: 0 6px 20px rgba(42, 71, 56, 0.06);
        --bk-card-radius: 18px;
        --bk-card-backdrop: none;
        --bk-text: #223028;
        --bk-muted: #5f7166;
        --bk-accent: #3f6a54;
        --bk-accent-text: #ffffff;
        --bk-surface: #eff4ed;
        --bk-header-bg: #3f6a54;
        --bk-header-text: #f7faf6;
        --bk-header-border: none;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: Georgia, serif;
        --bk-font-num: inherit;
        --bk-btn-radius: 12px;
        --bk-pill-radius: 999px;
        --bk-input-bg: #f6f9f5;
        --bk-input-border: #c4d3c0;
      }
    `,
  },
  {
    id: "pastel-cloud",
    nameKo: "파스텔 클라우드",
    nameEn: "Pastel Cloud",
    descKo: "하늘빛·라벤더 그라데이션과 푹신한 구름 카드",
    descEn: "Soft sky-lavender tones and pillowy rounded cards",
    swatch: { bg: "#f3f0ff", card: "#ffffff", accent: "#8b5cf6", border: "#e4ddff", radius: "26px" },
    css: `
      :host {
        --bk-bg: #f3f0ff;
        --bk-bg-image: linear-gradient(160deg, #eff6ff 0%, #f5f0ff 55%, #fff1f5 100%);
        --bk-card: #ffffff;
        --bk-card-border: 1px solid #e9e3ff;
        --bk-card-shadow: 0 12px 30px rgba(139, 92, 246, 0.09);
        --bk-card-radius: 26px;
        --bk-card-backdrop: none;
        --bk-text: #312e4a;
        --bk-muted: #706b91;
        --bk-accent: #8b5cf6;
        --bk-accent-text: #ffffff;
        --bk-surface: #f7f4ff;
        --bk-header-bg: linear-gradient(90deg, #8b5cf6, #ec4899);
        --bk-header-text: #ffffff;
        --bk-header-border: none;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: inherit;
        --bk-font-num: inherit;
        --bk-btn-radius: 999px;
        --bk-pill-radius: 999px;
        --bk-input-bg: #faf8ff;
        --bk-input-border: #dcd4ff;
      }
      .stat { border-radius: 18px !important; }
    `,
  },
  {
    id: "retro-terminal",
    nameKo: "레트로 터미널",
    nameEn: "Retro Terminal",
    descKo: "모노스페이스 폰트, 각진 프레임, CRT 그린 감성",
    descEn: "Monospace CRT phosphor green, sharp 0px geometry",
    swatch: { bg: "#0a0f0d", card: "#0f1914", accent: "#22c55e", border: "#1f4d34", radius: "0px" },
    css: `
      :host {
        --bk-bg: #0a0f0d;
        --bk-bg-image: repeating-linear-gradient(0deg, rgba(34, 197, 94, 0.04) 0px, rgba(34, 197, 94, 0.04) 1px, transparent 1px, transparent 4px);
        --bk-card: #0f1914;
        --bk-card-border: 1px solid #1f4d34;
        --bk-card-shadow: 0 0 12px rgba(34, 197, 94, 0.08);
        --bk-card-radius: 0px;
        --bk-card-backdrop: none;
        --bk-text: #bbf7d0;
        --bk-muted: #4ade80;
        --bk-accent: #22c55e;
        --bk-accent-text: #05110a;
        --bk-surface: #0b130f;
        --bk-header-bg: #0b130f;
        --bk-header-text: #4ade80;
        --bk-header-border: 1px solid #22c55e;
        --bk-font-body: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        --bk-font-head: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        --bk-font-num: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        --bk-btn-radius: 0px;
        --bk-pill-radius: 0px;
        --bk-input-bg: #070d0a;
        --bk-input-border: #22c55e;
      }
      .btn-top { background: #22c55e !important; color: #05110a !important; font-weight: 700; }
      .stat { border: 1px solid #163a27; }
    `,
  },
  {
    id: "warm-terracotta",
    nameKo: "웜 테라코타",
    nameEn: "Warm Terracotta",
    descKo: "점토·샌드 컬러와 상단 액센트 스트립",
    descEn: "Sun-baked clay palette with top-accented cards",
    swatch: { bg: "#f9f1e9", card: "#fffaf5", accent: "#c2593a", border: "#ead8c8", radius: "10px" },
    css: `
      :host {
        --bk-bg: #f9f1e9;
        --bk-bg-image: none;
        --bk-card: #fffaf5;
        --bk-card-border: 1px solid #ead8c8;
        --bk-card-shadow: 0 6px 18px rgba(138, 72, 46, 0.07);
        --bk-card-radius: 10px;
        --bk-card-backdrop: none;
        --bk-text: #3b261d;
        --bk-muted: #846254;
        --bk-accent: #c2593a;
        --bk-accent-text: #fffaf5;
        --bk-surface: #f5e9dc;
        --bk-header-bg: #3b261d;
        --bk-header-text: #fffaf5;
        --bk-header-border: none;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: Georgia, serif;
        --bk-font-num: inherit;
        --bk-btn-radius: 6px;
        --bk-pill-radius: 6px;
        --bk-input-bg: #fffdf9;
        --bk-input-border: #dec6b2;
      }
      .card { border-top: 3px solid #c2593a !important; }
    `,
  },
  {
    id: "tokyo-minimal",
    nameKo: "도쿄 미니멀",
    nameEn: "Tokyo Minimal",
    descKo: "그림자 없는 절제된 모노크롬과 주홍 포인트",
    descEn: "Shadowless architectural monochrome with vermilion accent",
    swatch: { bg: "#f7f7f5", card: "#ffffff", accent: "#d9381e", border: "#e2e2dd", radius: "2px" },
    css: `
      :host {
        --bk-bg: #f7f7f5;
        --bk-bg-image: none;
        --bk-card: #ffffff;
        --bk-card-border: 1px solid #e2e2dd;
        --bk-card-shadow: none;
        --bk-card-radius: 2px;
        --bk-card-backdrop: none;
        --bk-text: #181818;
        --bk-muted: #70706c;
        --bk-accent: #d9381e;
        --bk-accent-text: #ffffff;
        --bk-surface: #f7f7f5;
        --bk-header-bg: #ffffff;
        --bk-header-text: #181818;
        --bk-header-border: 1px solid #181818;
        --bk-font-body: system-ui, -apple-system, sans-serif;
        --bk-font-head: inherit;
        --bk-font-num: ui-monospace, SFMono-Regular, Menlo, monospace;
        --bk-btn-radius: 2px;
        --bk-pill-radius: 2px;
        --bk-input-bg: #ffffff;
        --bk-input-border: #c8c8c2;
      }
      .btn-top { background: #181818 !important; color: #fff !important; }
      .pill.active { background: #181818 !important; color: #fff !important; }
      .tab.active { background: #181818 !important; color: #fff !important; }
      .stat-val { color: #d9381e; }
    `,
  },
];

export function getThemeCss(themeId) {
  const found = THEMES.find((t) => t.id === themeId) || THEMES[0];
  return found.css;
}
