/* SZD-HTR Viewer — Katalog + Viewer + Edit */
'use strict';

/* ===== Constants ===== */

const ITEMS_PER_PAGE = 50;
const GAMS_BASE = 'https://gams.uni-graz.at/';
const SEARCH_DEBOUNCE_MS = 150;

const COLLECTION_LABELS = {
  lebensdokumente: 'Lebensdokumente',
  werke: 'Werke',
  aufsatzablage: 'Aufsatzablage',
  korrespondenzen: 'Korrespondenzen',
};

const LS_KEY = 'szd-htr-edits';
const LS_GT_KEY = 'szd-htr-gt-reviews';
const LS_FIT_KEY = 'szd-htr-fit-mode';

const CONSENSUS_SHORT = { consensus_verified: 'Verifiz.', consensus_moderate: 'Moderat', consensus_review: 'Review', consensus_divergent: 'Divergent' };
const CONSENSUS_LABELS = { consensus_verified: 'Verifiziert', consensus_moderate: 'Moderat', consensus_review: 'Review', consensus_divergent: 'Divergent' };
const CONSENSUS_TOOLTIPS = { consensus_verified: 'Konsensus: verifiziert', consensus_moderate: 'Konsensus: moderat', consensus_review: 'Konsensus: Review', consensus_divergent: 'Konsensus: divergent' };

/* ===== State ===== */

const state = {
  catalog: [],
  collections: [],
  collectionData: {},       // cached: { "werke": { objects: [...] }, ... }
  filteredObjects: [],
  currentObjectId: null,
  currentPage: 0,
  catalogPage: 0,
  searchQuery: '',
  sortField: 'collection',
  sortAsc: true,
  filterCollection: '',
  filterGroup: '',
  filterConfidence: '',
  filterReviewStatus: '',
  filterConsensus: '',
  editMode: false,
  diffMode: false,
  gtReviewMode: false,
  hasReviewData: false,
  hasConsensusData: false,
  editedTranscriptions: new Map(),
  gtReviews: new Map(),       // objectId:page → { transcription, approved, source }
  gtData: null,               // loaded from groundtruth.json
  knowledgeData: null,         // loaded from knowledge.json
  isLocal: false,
  fitMode: 'height',         // 'height' or 'width'
};

/* ===== Utilities ===== */

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderTranscription(text) {
  if (!text) return '';
  return escapeHtml(text).replace(/~~(.+?)~~/g, '<del>$1</del>');
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

function editKey(objectId, page) {
  return `${objectId}:${page}`;
}

function showToast(message, durationMs = 2000) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('visible');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('visible'), durationMs);
}

/* ===== Local Detection ===== */

function detectLocal() {
  const h = location.hostname;
  state.isLocal = h === 'localhost' || h === '127.0.0.1' || h === '' || location.protocol === 'file:';
}

/* ===== Fit Mode ===== */

function loadFitMode() {
  try {
    const saved = localStorage.getItem(LS_FIT_KEY);
    if (saved === 'width' || saved === 'height') state.fitMode = saved;
  } catch { /* ignore */ }
}

function applyFitMode() {
  const panel = document.getElementById('imgPanel');
  if (!panel) return;
  panel.classList.toggle('fit-height', state.fitMode === 'height');
  panel.classList.toggle('fit-width', state.fitMode === 'width');
  const btn = document.getElementById('navFitBtn');
  if (btn) {
    btn.dataset.tooltip = state.fitMode === 'height' ? 'Breite einpassen' : 'H\u00f6he einpassen';
  }
}

function toggleFitMode() {
  state.fitMode = state.fitMode === 'height' ? 'width' : 'height';
  try { localStorage.setItem(LS_FIT_KEY, state.fitMode); } catch { /* ignore */ }
  applyFitMode();
}

/* ===== localStorage ===== */

function loadEditsFromStorage() {
  if (!state.isLocal) return;
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) {
      const entries = JSON.parse(raw);
      state.editedTranscriptions = new Map(entries);
    }
  } catch { /* ignore */ }
}

function saveEditsToStorage() {
  if (!state.isLocal) return;
  try {
    const entries = [...state.editedTranscriptions.entries()];
    localStorage.setItem(LS_KEY, JSON.stringify(entries));
  } catch { /* ignore */ }
}

function getEditCount(objectId) {
  let count = 0;
  for (const key of state.editedTranscriptions.keys()) {
    if (key.startsWith(objectId + ':')) count++;
  }
  return count;
}

/* ===== Data Loading ===== */

async function loadCatalog() {
  const resp = await fetch('catalog.json');
  if (!resp.ok) throw new Error('Katalog nicht gefunden');
  const data = await resp.json();
  state.catalog = data.objects || [];
  state.collections = data.collections || [];
}

async function loadCollectionData(collection) {
  if (state.collectionData[collection]) return state.collectionData[collection];
  const resp = await fetch(`data/${collection}.json`);
  if (!resp.ok) throw new Error(`Sammlung '${collection}' nicht gefunden`);
  const data = await resp.json();
  state.collectionData[collection] = data;
  return data;
}

function getViewerObject(objectId) {
  const catalogObj = state.catalog.find(o => o.id === objectId);
  if (!catalogObj) return null;
  const colData = state.collectionData[catalogObj.collection];
  if (!colData) return null;
  const detail = colData.objects.find(o => o.id === objectId);
  if (!detail) return null;
  return { ...catalogObj, ...detail };
}

/* ===== Router ===== */

function parseHash() {
  const hash = location.hash.slice(1);
  if (hash === 'help') return { view: 'help' };
  if (!hash || hash.startsWith('catalog')) {
    return { view: 'catalog', objectId: null, page: 0 };
  }
  if (hash === 'knowledge') return { view: 'knowledge' };
  const km = hash.match(/^knowledge\/(.+)$/);
  if (km) return { view: 'knowledge-doc', slug: km[1] };
  if (hash === 'about') return { view: 'about' };
  const m = hash.match(/^view\/(.+?)(?:\/(\d+))?$/);
  if (m) return { view: 'viewer', objectId: m[1], page: m[2] ? parseInt(m[2], 10) - 1 : 0 };
  return { view: 'catalog', objectId: null, page: 0 };
}

function navigate(hash) {
  if (location.hash === '#' + hash || (!location.hash && !hash)) return;
  location.hash = hash;
}

function buildCatalogHash() {
  const params = new URLSearchParams();
  if (state.filterCollection) params.set('collection', state.filterCollection);
  if (state.filterGroup) params.set('group', state.filterGroup);
  if (state.filterConfidence) params.set('confidence', state.filterConfidence);
  if (state.filterReviewStatus) params.set('review_status', state.filterReviewStatus);
  if (state.filterConsensus) params.set('consensus', state.filterConsensus);
  if (state.searchQuery) params.set('q', state.searchQuery);
  if (state.sortField !== 'collection') params.set('sort', state.sortField);
  if (!state.sortAsc) params.set('asc', '0');
  if (state.catalogPage > 0) params.set('page', String(state.catalogPage + 1));
  const qs = params.toString();
  return qs ? 'catalog?' + qs : '';
}

function parseCatalogParams(hash) {
  const qIdx = hash.indexOf('?');
  if (qIdx === -1) return;
  const params = new URLSearchParams(hash.slice(qIdx + 1));
  if (params.has('collection')) state.filterCollection = params.get('collection');
  if (params.has('group')) state.filterGroup = params.get('group');
  if (params.has('confidence')) state.filterConfidence = params.get('confidence');
  if (params.has('review_status')) state.filterReviewStatus = params.get('review_status');
  if (params.get('review') === '1') state.filterReviewStatus = 'needs_review';
  if (params.has('consensus')) state.filterConsensus = params.get('consensus');
  if (params.has('q')) state.searchQuery = params.get('q');
  if (params.has('sort')) state.sortField = params.get('sort');
  if (params.has('asc')) state.sortAsc = params.get('asc') !== '0';
  if (params.has('page')) state.catalogPage = Math.max(0, parseInt(params.get('page'), 10) - 1);
}

function restoreFilterUI() {
  document.getElementById('searchInput').value = state.searchQuery;
  document.getElementById('filterCollection').value = state.filterCollection;
  updateGroupFilter();
  document.getElementById('filterGroup').value = state.filterGroup;
  document.getElementById('filterConfidence').value = state.filterConfidence;
  document.getElementById('filterReviewStatus').value = state.filterReviewStatus;
  document.getElementById('filterConsensus').value = state.filterConsensus;
}

function updateCatalogURL() {
  const newHash = buildCatalogHash();
  const currentHash = location.hash.slice(1);
  if (currentHash !== newHash) {
    history.replaceState(null, '', '#' + newHash);
  }
}

function route() {
  const r = parseHash();
  if (r.view === 'viewer' && r.objectId) {
    showViewer(r.objectId, r.page);
  } else if (r.view === 'knowledge') {
    showKnowledgeIndex();
  } else if (r.view === 'knowledge-doc' && r.slug) {
    showKnowledgeDoc(r.slug);
  } else if (r.view === 'about') {
    showAbout();
  } else if (r.view === 'help') {
    showHelp();
  } else {
    parseCatalogParams(location.hash.slice(1));
    restoreFilterUI();
    showCatalog();
    renderCatalog();
  }
}

function resetDiffMode() {
  if (!state.diffMode) return;
  state.diffMode = false;
  const diffPanel = document.getElementById('diffPanel');
  const textPanel = document.getElementById('textPanel');
  const labelRight = document.getElementById('panelLabelRight');
  const diffBtn = document.getElementById('diffBtn');
  if (diffPanel) diffPanel.style.display = 'none';
  if (textPanel) textPanel.style.display = '';
  if (labelRight) labelRight.textContent = 'Transkription';
  if (diffBtn) diffBtn.classList.remove('active');
}

function showCatalog() {
  document.body.className = 'view-catalog';
  document.title = 'SZD-HTR — Katalog';
  state.currentObjectId = null;
  state.editMode = false;
  resetDiffMode();
  requestAnimationFrame(() => document.getElementById('searchInput')?.focus());
}

async function showViewer(objectId, page) {
  document.body.className = 'view-viewer';
  state.currentObjectId = objectId;
  state.currentPage = page || 0;
  state.editMode = false;
  resetDiffMode();

  const catalogObj = state.catalog.find(o => o.id === objectId);
  if (!catalogObj) {
    document.getElementById('viewerPanels').innerHTML =
      '<div class="loading" style="grid-column:1/-1">Objekt nicht gefunden.</div>';
    return;
  }

  document.title = `SZD-HTR — ${catalogObj.titleClean || catalogObj.label}`;

  // Load collection data if needed
  if (!state.collectionData[catalogObj.collection]) {
    document.getElementById('viewerPanels').classList.add('loading-data');
    try {
      await loadCollectionData(catalogObj.collection);
    } catch {
      document.getElementById('viewerPanels').classList.remove('loading-data');
      document.getElementById('transcription').textContent = 'Fehler beim Laden der Daten.';
      return;
    }
    document.getElementById('viewerPanels').classList.remove('loading-data');
  }

  // Skip blank/color_chart pages at start — jump to first content page
  if (state.currentPage === 0) {
    const viewObj = getViewerObject(objectId);
    if (viewObj && viewObj.pages) {
      const firstContentIdx = viewObj.pages.findIndex(p => !p.type || p.type === 'content');
      if (firstContentIdx > 0) {
        state.currentPage = firstContentIdx;
        history.replaceState(null, '', `#view/${objectId}/${firstContentIdx + 1}`);
      }
    }
  }

  renderViewerMeta(getViewerObject(objectId) || catalogObj);
  renderViewerNav();
  renderViewerPage();
  updateEditButtons();
  requestAnimationFrame(() => document.getElementById('viewerMeta')?.focus());
}

/* ===== Knowledge Vault + About ===== */

async function ensureKnowledgeData() {
  if (state.knowledgeData) return;
  try {
    const resp = await fetch('data/knowledge.json');
    if (!resp.ok) throw new Error('Knowledge data not found');
    state.knowledgeData = await resp.json();
  } catch {
    state.knowledgeData = { docs: {}, sections: [], about: { html: '' } };
  }
}

async function showKnowledgeIndex() {
  document.body.className = 'view-knowledge';
  document.title = 'SZD-HTR \u2014 Research Vault';
  state.currentObjectId = null;
  state.editMode = false;
  resetDiffMode();
  await ensureKnowledgeData();
  renderKnowledgeIndex();
}

function renderKnowledgeIndex() {
  const el = document.getElementById('knowledgeSections');
  if (!el || !state.knowledgeData) return;

  const { sections, docs } = state.knowledgeData;
  let html = '';

  for (const sec of sections) {
    html += `<div class="knowledge__section">
      <div class="knowledge__section-label">${escapeHtml(sec.label)}</div>
      <div class="knowledge__cards">`;

    for (const slug of sec.slugs) {
      const doc = docs[slug];
      if (!doc) continue;
      const statusCls = 'knowledge__badge--' + (doc.status || 'draft');
      html += `<a href="#knowledge/${slug}" class="knowledge__card">
        <div class="knowledge__card-title">${escapeHtml(doc.title)}</div>
        <div class="knowledge__card-meta">
          <span class="knowledge__badge knowledge__badge--type">${escapeHtml(doc.type)}</span>
          <span class="knowledge__badge ${statusCls}">${escapeHtml(doc.status)}</span>
          <span class="knowledge__card-words">${doc.wordCount || 0} W\u00f6rter</span>
        </div>
      </a>`;
    }

    html += '</div></div>';
  }

  // Show docs not in any section
  const allSectioned = new Set(sections.flatMap(s => s.slugs));
  const unsectioned = Object.values(docs).filter(d => !allSectioned.has(d.slug));
  if (unsectioned.length > 0) {
    html += `<div class="knowledge__section">
      <div class="knowledge__section-label">Weitere Dokumente</div>
      <div class="knowledge__cards">`;
    for (const doc of unsectioned) {
      const statusCls = 'knowledge__badge--' + (doc.status || 'draft');
      html += `<a href="#knowledge/${doc.slug}" class="knowledge__card">
        <div class="knowledge__card-title">${escapeHtml(doc.title)}</div>
        <div class="knowledge__card-meta">
          <span class="knowledge__badge knowledge__badge--type">${escapeHtml(doc.type)}</span>
          <span class="knowledge__badge ${statusCls}">${escapeHtml(doc.status)}</span>
          <span class="knowledge__card-words">${doc.wordCount || 0} W\u00f6rter</span>
        </div>
      </a>`;
    }
    html += '</div></div>';
  }

  el.innerHTML = html;
}

async function showKnowledgeDoc(slug) {
  document.body.className = 'view-knowledge-doc';
  state.currentObjectId = null;
  state.editMode = false;
  resetDiffMode();
  await ensureKnowledgeData();

  const doc = state.knowledgeData?.docs?.[slug];
  if (!doc) {
    document.getElementById('knowledgeDocContent').innerHTML =
      '<p>Dokument nicht gefunden.</p>';
    document.getElementById('knowledgeDocSidebar').innerHTML =
      `<div class="knowledge-doc__sidebar-nav"><a href="#knowledge">\u2190 Vault</a></div>`;
    return;
  }

  document.title = `SZD-HTR \u2014 ${doc.title}`;
  renderKnowledgeDoc(doc);
  // Scroll to top
  window.scrollTo(0, 0);
}

function renderKnowledgeDoc(doc) {
  const sidebar = document.getElementById('knowledgeDocSidebar');
  const content = document.getElementById('knowledgeDocContent');
  if (!sidebar || !content) return;

  // Navigation: back to index
  let sidebarHtml = `<div class="knowledge-doc__sidebar-nav">
    <a href="#knowledge">\u2190 Vault</a>`;

  // Prev/Next based on reading order
  const { sections } = state.knowledgeData;
  const allSlugs = sections.flatMap(s => s.slugs);
  const idx = allSlugs.indexOf(doc.slug);
  if (idx > 0) {
    const prev = state.knowledgeData.docs[allSlugs[idx - 1]];
    if (prev) sidebarHtml += `<a href="#knowledge/${prev.slug}" title="${escapeHtml(prev.title)}">\u2190</a>`;
  }
  if (idx >= 0 && idx < allSlugs.length - 1) {
    const next = state.knowledgeData.docs[allSlugs[idx + 1]];
    if (next) sidebarHtml += `<a href="#knowledge/${next.slug}" title="${escapeHtml(next.title)}">\u2192</a>`;
  }
  sidebarHtml += '</div>';

  // Metadata
  const statusCls = 'knowledge__badge--' + (doc.status || 'draft');
  sidebarHtml += `<dl class="knowledge-doc__sidebar-meta">
    <dt>Typ</dt><dd><span class="knowledge__badge knowledge__badge--type">${escapeHtml(doc.type)}</span></dd>
    <dt>Status</dt><dd><span class="knowledge__badge ${statusCls}">${escapeHtml(doc.status)}</span></dd>
    <dt>Erstellt</dt><dd>${escapeHtml(doc.created)}</dd>
    <dt>Aktualisiert</dt><dd>${escapeHtml(doc.updated)}</dd>`;

  if (doc.tags && doc.tags.length > 0) {
    sidebarHtml += `<dt>Tags</dt><dd>${doc.tags.map(t => escapeHtml(t)).join(', ')}</dd>`;
  }

  if (doc.related && doc.related.length > 0) {
    const links = doc.related.map(relSlug => {
      const rd = state.knowledgeData.docs[relSlug];
      const title = rd ? rd.title : relSlug;
      return `<a href="#knowledge/${relSlug}">${escapeHtml(title)}</a>`;
    }).join('<br>');
    sidebarHtml += `<dt>Verwandt</dt><dd>${links}</dd>`;
  }
  sidebarHtml += '</dl>';

  // TOC from headings
  if (doc.headings && doc.headings.length > 0) {
    sidebarHtml += `<div class="knowledge-doc__toc">
      <div class="knowledge-doc__toc-title">Inhalt</div>
      <ul class="knowledge-doc__toc-list">`;
    for (const h of doc.headings) {
      const lvlCls = h.level >= 3 ? ` toc-h${h.level}` : '';
      sidebarHtml += `<li><a href="#${h.id}" class="${lvlCls}">${escapeHtml(h.text)}</a></li>`;
    }
    sidebarHtml += '</ul></div>';
  }

  sidebar.innerHTML = sidebarHtml;
  content.innerHTML = doc.html;

  // Smooth-scroll TOC links
  sidebar.querySelectorAll('.knowledge-doc__toc-list a').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const targetId = a.getAttribute('href').slice(1);
      const target = document.getElementById(targetId);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

async function showAbout() {
  document.body.className = 'view-about';
  document.title = 'SZD-HTR \u2014 Projekt';
  state.currentObjectId = null;
  state.editMode = false;
  resetDiffMode();
  await ensureKnowledgeData();

  const el = document.getElementById('aboutContent');
  if (el && state.knowledgeData?.about) {
    el.innerHTML = state.knowledgeData.about.html;
  }
}

/* ===== Review / Quality Signals ===== */

function renderReviewCell(obj) {
  // Tier 0: GT verified (highest)
  if (obj.gtVerified) {
    return '<span class="badge-review badge-review-verified" data-tooltip="Ground Truth verifiziert">GT \u2713</span>';
  }
  // Tier 1: Human expert approved
  if (obj.reviewStatus === 'approved') {
    return '<span class="badge-review badge-review-approved" data-tooltip="Human-Expert hat verifiziert">Gepr\u00fcft</span>';
  }
  if (obj.needsReview === undefined) return '';
  // Tier 2: Quality signals flagged problems
  if (obj.needsReview) {
    const reasons = (obj.needsReviewReasons || []).join(', ') || 'quality_signals hat Probleme erkannt';
    return `<span class="badge-review badge-review-yes" data-tooltip="${escapeHtml(reasons)}">Review</span>`;
  }
  // Tier 3: Machine says OK, no human check
  return '<span class="badge-review badge-review-llm-ok" data-tooltip="LLM-Transkription ohne manuelle Pr\u00fcfung">LLM OK</span>';
}

function renderQualitySignals(qs) {
  if (!qs) return '';
  const items = [];

  // needs_review
  if (qs.needs_review !== undefined) {
    if (qs.needs_review) {
      items.push(`<div class="viewer__quality-item">
        <span class="badge-review badge-review-yes">Review empfohlen</span></div>`);
    } else {
      items.push(`<div class="viewer__quality-item">
        <span class="badge-review badge-review-llm-ok">LLM OK</span></div>`);
    }
  }

  // marker density
  if (qs.marker_density !== undefined) {
    const pct = (qs.marker_density * 100).toFixed(1);
    items.push(`<div class="viewer__quality-item">
      <span class="viewer__quality-label">Marker</span>
      <span>${qs.marker_uncertain_count || 0}\u00d7 [?], ${qs.marker_illegible_count || 0}\u00d7 [...] (${pct}%)</span></div>`);
  }

  // empty pages
  if (qs.empty_pages > 0) {
    items.push(`<div class="viewer__quality-item">
      <span class="viewer__quality-label">Leer</span>
      <span>${qs.empty_pages} / ${qs.total_pages || '?'} Seiten</span></div>`);
  }

  // language match
  if (qs.language_match !== undefined) {
    const icon = qs.language_match ? '' : ' \u26A0';
    const text = qs.language_match
      ? qs.language_detected || '?'
      : `${qs.language_detected || '?'} (erwartet: ${qs.language_expected || '?'})`;
    items.push(`<div class="viewer__quality-item">
      <span class="viewer__quality-label">Sprache</span>
      <span>${escapeHtml(text)}${icon}</span></div>`);
  }

  // text volume
  if (qs.total_chars) {
    items.push(`<div class="viewer__quality-item">
      <span class="viewer__quality-label">Umfang</span>
      <span>${qs.total_chars.toLocaleString('de')} Zeichen, ${qs.total_words || '?'} Wörter</span></div>`);
  }

  // DWR score
  if (qs.dwr_score !== undefined && qs.dwr_score > 0) {
    const pct = Math.round(qs.dwr_score * 100);
    const cls = pct >= 30 ? 'badge-dwr-good' : pct >= 15 ? 'badge-dwr-moderate' : 'badge-dwr-low';
    items.push(`<div class="viewer__quality-item">
      <span class="viewer__quality-label">DWR</span>
      <span class="badge ${cls}">${pct}%</span></div>`);
  }

  let html = `<div class="viewer__quality"><div class="viewer__quality-grid">${items.join('')}</div>`;

  // reasons
  if (qs.needs_review && qs.needs_review_reasons && qs.needs_review_reasons.length > 0) {
    const lis = qs.needs_review_reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('');
    html += `<div class="viewer__quality-reasons"><ul>${lis}</ul></div>`;
  }

  html += '</div>';
  return html;
}

/* ===== Quality Rendering ===== */

function renderQualityCell(v, confidence, obj) {
  const uncertain = v.uncertainCount || 0;
  const illegible = v.illegibleCount || 0;
  const total = uncertain + illegible;

  let markerHtml;
  if (total === 0) {
    markerHtml = '<span class="badge badge-markers badge-markers-clean" data-tooltip="Keine unsicheren Stellen im Text">—</span>';
  } else {
    const parts = [];
    if (uncertain > 0) parts.push(`${uncertain}\u00d7 [?]`);
    if (illegible > 0) parts.push(`${illegible}\u00d7 [...]`);
    const cls = total >= 3 ? 'badge-markers-many' : 'badge-markers-some';
    const tooltip = parts.join(', ') + ` in ${v.totalChars || '?'} Zeichen`;
    markerHtml = `<span class="badge badge-markers ${cls}" data-tooltip="${tooltip}">${parts.join(', ')}</span>`;
  }

  const vlmTooltip = 'VLM-Selbsteinschätzung (schwaches Signal)';
  const vlmHtml = confidence
    ? ` <span class="badge badge-vlm" data-tooltip="${vlmTooltip}">${confidence}</span>`
    : '';

  // Consensus badge
  let consHtml = '';
  if (obj && obj.consensusCategory) {
    const cat = obj.consensusCategory;
    const cls = 'badge-consensus-' + cat.replace('consensus_', '');
    consHtml = ` <span class="badge badge-consensus ${cls}" data-tooltip="${CONSENSUS_TOOLTIPS[cat] || cat}">${CONSENSUS_SHORT[cat] || '?'}</span>`;
  }

  return markerHtml + vlmHtml + consHtml;
}

/* ===== Stats Dashboard ===== */

function renderStats() {
  const el = document.getElementById('catalogStats');
  if (!el || state.catalog.length === 0) return;

  const total = state.catalog.length;

  // Aggregate all statistics in a single pass
  const perCol = {};
  for (const col of state.collections) perCol[col] = 0;
  const perGroup = {};
  const confDist = { high: 0, medium: 0, low: 0 };
  let reviewCount = 0, verifiedCount = 0, approvedCount = 0, llmOkCount = 0;
  let totalPages = 0, totalContentPages = 0, totalBlankPages = 0;
  let totalChars = 0;
  let dwrSum = 0, dwrCount = 0;
  let consensusCount = 0;
  const consCatDist = {};

  for (const o of state.catalog) {
    perCol[o.collection] = (perCol[o.collection] || 0) + 1;
    const g = o.classification || o.groupLabel || '?';
    perGroup[g] = (perGroup[g] || 0) + 1;
    if (o.needsReview) reviewCount++;
    if (o.gtVerified) verifiedCount++;
    if (o.reviewStatus === 'approved') approvedCount++;
    if (o.needsReview === false && !o.gtVerified && o.reviewStatus !== 'approved') llmOkCount++;
    if (o.confidence) confDist[o.confidence] = (confDist[o.confidence] || 0) + 1;
    totalPages += o.pageCount || 0;
    totalContentPages += o.contentPages || 0;
    totalBlankPages += o.blankPages || 0;
    totalChars += (o.verification || {}).totalChars || 0;
    if (o.dwrScore > 0) { dwrSum += o.dwrScore; dwrCount++; }
    if (o.consensusCategory) {
      consensusCount++;
      consCatDist[o.consensusCategory] = (consCatDist[o.consensusCategory] || 0) + 1;
    }
  }

  const reviewPct = total > 0 ? Math.round((reviewCount / total) * 100) : 0;
  const avgDwr = dwrCount > 0 ? Math.round((dwrSum / dwrCount) * 100) : 0;

  // Summary line: chips for collections
  const colChips = state.collections.map(c => {
    const label = COLLECTION_LABELS[c] || c;
    return `<span class="catalog__stats-chip"><strong>${perCol[c]}</strong> ${escapeHtml(label)}</span>`;
  }).join('');

  const reviewChip = state.hasReviewData && reviewCount > 0
    ? `<span class="catalog__stats-chip catalog__stats-chip--review-warn"><strong>${reviewCount}</strong> Review</span>`
    : '';
  const llmOkChip = llmOkCount > 0
    ? `<span class="catalog__stats-chip catalog__stats-chip--llm-ok"><strong>${llmOkCount}</strong> LLM OK</span>`
    : '';
  const approvedChip = approvedCount > 0
    ? `<span class="catalog__stats-chip catalog__stats-chip--approved"><strong>${approvedCount}</strong> Gepr\u00fcft</span>`
    : '';
  const verifiedChip = verifiedCount > 0
    ? `<span class="catalog__stats-chip catalog__stats-chip--verified"><strong>${verifiedCount}</strong> GT \u2713</span>`
    : '';
  const consensusChip = consensusCount > 0
    ? `<span class="catalog__stats-chip catalog__stats-chip--consensus"><strong>${consensusCount}</strong> Konsensus</span>`
    : '';

  // Detail section: groups
  const groupEntries = Object.entries(perGroup).sort((a, b) => b[1] - a[1]);
  const groupItems = groupEntries.map(([g, n]) =>
    `<span class="catalog__stats-bar-item"><strong>${n}</strong> ${escapeHtml(g)}</span>`
  ).join('');

  // Confidence distribution
  const confItems = ['high', 'medium', 'low'].map(c => {
    if (!confDist[c]) return '';
    const cls = c === 'high' ? 'badge-markers-clean' : c === 'medium' ? 'badge-markers-some' : 'badge-markers-many';
    return `<span class="catalog__stats-bar-item"><span class="badge ${cls}" style="font-size:0.68rem">${confDist[c]}</span> ${c}</span>`;
  }).filter(Boolean).join('');

  // Page stats
  const colorChartPages = totalPages - totalContentPages - totalBlankPages;
  const pageItems = `
    <span class="catalog__stats-bar-item"><strong>${totalPages.toLocaleString('de')}</strong> Seiten</span>
    <span class="catalog__stats-bar-item"><strong>${totalContentPages.toLocaleString('de')}</strong> Inhalt</span>
    <span class="catalog__stats-bar-item"><strong>${totalBlankPages.toLocaleString('de')}</strong> Leer</span>
    ${colorChartPages > 0 ? `<span class="catalog__stats-bar-item"><strong>${colorChartPages}</strong> Farbskala</span>` : ''}
    <span class="catalog__stats-bar-item"><strong>${totalChars.toLocaleString('de')}</strong> Zeichen</span>`;

  // Review stats (3-tier)
  const humanCount = approvedCount + verifiedCount;
  let reviewItems = '';
  if (state.hasReviewData) {
    reviewItems = `<span class="catalog__stats-bar-item"><strong>${humanCount}</strong> Human Verified</span>
      <span class="catalog__stats-bar-item"><strong>${llmOkCount}</strong> LLM OK</span>
      <span class="catalog__stats-bar-item"><strong>${reviewCount}</strong> Needs Review (${reviewPct}%)</span>`;
  }

  // DWR + Consensus
  const dwrItem = dwrCount > 0
    ? `<span class="catalog__stats-bar-item"><strong>${avgDwr}%</strong> \u00D8 DWR (${dwrCount} Objekte)</span>`
    : '';

  let consItems = '';
  if (consensusCount > 0) {
    const cats = Object.entries(consCatDist).map(([cat, n]) =>
      `<span class="catalog__stats-bar-item"><strong>${n}</strong> ${CONSENSUS_LABELS[cat] || cat}</span>`
    ).join('');
    consItems = `<span class="catalog__stats-bar-item"><strong>${consensusCount}</strong> / ${total} mit Konsensus</span>${cats}`;
  }

  el.innerHTML = `
    <div class="catalog__stats-summary">
      <span class="catalog__stats-total">${total} Objekte</span>
      <div class="catalog__stats-chips">${colChips}${verifiedChip}${approvedChip}${llmOkChip}${reviewChip}${consensusChip}</div>
      <button type="button" class="catalog__stats-toggle" id="statsToggle" aria-expanded="false">Details &#9662;</button>
    </div>
    <div class="catalog__stats-details" id="statsDetails">
      <div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Seiten &amp; Umfang</div>
        <div class="catalog__stats-bar">${pageItems}</div>
      </div>
      <div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Nach Typ</div>
        <div class="catalog__stats-bar">${groupItems}</div>
      </div>
      <div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Konfidenz</div>
        <div class="catalog__stats-bar">${confItems}</div>
      </div>
      ${reviewItems ? `<div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Review</div>
        <div class="catalog__stats-bar">${reviewItems}${dwrItem ? ` ${dwrItem}` : ''}</div>
      </div>` : ''}
      ${consItems ? `<div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Konsensus-Verifikation</div>
        <div class="catalog__stats-bar">${consItems}</div>
      </div>` : ''}
    </div>`;

  el.style.display = 'block';

  document.getElementById('statsToggle').addEventListener('click', () => {
    const details = document.getElementById('statsDetails');
    const toggle = document.getElementById('statsToggle');
    const open = details.classList.toggle('open');
    toggle.innerHTML = open ? 'Weniger &#9652;' : 'Details &#9662;';
    toggle.setAttribute('aria-expanded', String(open));
  });
}

/* ===== Catalog Rendering ===== */

function applyFilters() {
  let list = state.catalog;

  if (state.filterCollection) {
    list = list.filter(o => o.collection === state.filterCollection);
  }
  if (state.filterGroup) {
    list = list.filter(o => (o.classification || o.groupLabel) === state.filterGroup);
  }
  if (state.filterConfidence) {
    list = list.filter(o => o.confidence === state.filterConfidence);
  }
  if (state.filterReviewStatus) {
    if (state.filterReviewStatus === 'human_verified') {
      list = list.filter(o => o.reviewStatus === 'approved' || o.gtVerified);
    } else if (state.filterReviewStatus === 'llm_ok') {
      list = list.filter(o => o.needsReview === false && !o.gtVerified && o.reviewStatus !== 'approved');
    } else if (state.filterReviewStatus === 'needs_review') {
      list = list.filter(o => o.needsReview);
    }
  }
  if (state.filterConsensus) {
    if (state.filterConsensus === 'none') {
      list = list.filter(o => !o.consensusCategory);
    } else {
      list = list.filter(o => o.consensusCategory === state.filterConsensus);
    }
  }
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    list = list.filter(o =>
      (o.titleClean || '').toLowerCase().includes(q) ||
      (o.signature || '').toLowerCase().includes(q) ||
      (o.pid || '').toLowerCase().includes(q)
    );
  }

  // Sort
  const field = state.sortField;
  const dir = state.sortAsc ? 1 : -1;
  const getValue = (o) => {
    if (field === 'classification') {
      return o.classification || o.groupLabel || '';
    }
    if (field === 'needsReview') {
      return o.needsReview ? 1 : 0;
    }
    if (field === 'markerCount') {
      const v = o.verification || {};
      return (v.uncertainCount || 0) + (v.illegibleCount || 0);
    }
    return o[field] ?? '';
  };
  list = [...list].sort((a, b) => {
    const va = getValue(a);
    const vb = getValue(b);
    if (typeof va === 'number') return (va - vb) * dir;
    return String(va).toLowerCase().localeCompare(String(vb).toLowerCase(), 'de') * dir;
  });

  state.filteredObjects = list;
}

function renderCatalog() {
  applyFilters();

  const total = state.filteredObjects.length;
  const totalPages = Math.max(1, Math.ceil(total / ITEMS_PER_PAGE));
  if (state.catalogPage >= totalPages) state.catalogPage = totalPages - 1;
  if (state.catalogPage < 0) state.catalogPage = 0;

  const start = state.catalogPage * ITEMS_PER_PAGE;
  const pageItems = state.filteredObjects.slice(start, start + ITEMS_PER_PAGE);

  const tbody = document.getElementById('catalogBody');
  const empty = document.getElementById('catalogEmpty');

  if (total === 0) {
    tbody.innerHTML = '';
    empty.style.display = '';
    document.querySelector('.catalog__table-wrap').style.display = 'none';
  } else {
    empty.style.display = 'none';
    document.querySelector('.catalog__table-wrap').style.display = '';

    let html = '';
    for (const obj of pageItems) {
      const v = obj.verification || {};
      const qualityHtml = renderQualityCell(v, obj.confidence, obj);
      const titleFull = escapeHtml(obj.titleClean || obj.label);
      html += `<tr data-id="${obj.id}" tabindex="0">
        <td class="col-thumb"><img src="${obj.thumbnail || ''}" loading="lazy" alt=""></td>
        <td class="col-title" data-tooltip="${escapeHtml(obj.title)}">${titleFull}</td>
        <td class="col-sig">${escapeHtml(obj.signature)}</td>
        <td class="col-pid">${escapeHtml(obj.pid)}</td>
        <td class="col-collection">${COLLECTION_LABELS[obj.collection] || obj.collection}</td>
        <td class="col-group" data-tooltip="${escapeHtml(obj.objecttyp || '')}">${escapeHtml(obj.classification || obj.groupLabel)}</td>
        <td class="col-lang">${escapeHtml(obj.lang)}</td>
        <td class="col-review">${renderReviewCell(obj)}</td>
        <td class="col-quality">${qualityHtml}</td>
        <td class="col-pages" data-tooltip="${obj.contentPages || obj.pageCount || 0} Inhalt, ${obj.blankPages || 0} Leer">${obj.pageCount || '—'}</td>
      </tr>`;
    }
    tbody.innerHTML = html;
  }

  // Pagination
  const info = document.getElementById('paginationInfo');
  const endIdx = Math.min(start + ITEMS_PER_PAGE, total);
  info.textContent = total > 0 ? `${start + 1}–${endIdx} von ${total}` : '';

  document.getElementById('prevPage').disabled = state.catalogPage === 0;
  document.getElementById('nextPage').disabled = state.catalogPage >= totalPages - 1;

  const pagesEl = document.getElementById('paginationPages');
  pagesEl.textContent = total > 0 ? `Seite ${state.catalogPage + 1} / ${totalPages}` : '';

  // Update group filter options based on current visible data
  updateGroupFilter();

  // Show review/consensus filters only if data supports them
  document.getElementById('filterReviewStatus').style.display = state.hasReviewData ? '' : 'none';
  document.getElementById('filterConsensus').style.display = state.hasConsensusData ? '' : 'none';

  // Show/hide clear button
  const hasFilters = state.searchQuery || state.filterCollection || state.filterGroup || state.filterConfidence || state.filterReviewStatus || state.filterConsensus;
  document.getElementById('clearFilters').style.display = hasFilters ? '' : 'none';

  // Sort indicators
  document.querySelectorAll('.catalog__table th[data-sort]').forEach(th => {
    const field = th.dataset.sort;
    const arrow = th.querySelector('.sort-arrow');
    if (!arrow) return;
    const isSorted = field === state.sortField;
    th.classList.toggle('sorted', isSorted);
    arrow.textContent = isSorted ? (state.sortAsc ? '\u25B4' : '\u25BE') : '\u25B4';
    if (isSorted) {
      th.setAttribute('aria-sort', state.sortAsc ? 'ascending' : 'descending');
    } else {
      th.removeAttribute('aria-sort');
    }
  });

  updateCatalogURL();
}

function initCatalogFilters() {
  const sel = document.getElementById('filterCollection');
  for (const col of state.collections) {
    const opt = document.createElement('option');
    opt.value = col;
    opt.textContent = COLLECTION_LABELS[col] || col;
    sel.appendChild(opt);
  }
  updateGroupFilter();
}

function updateGroupFilter() {
  const sel = document.getElementById('filterGroup');
  const prev = sel.value;

  // Get groups available in current collection filter
  let source = state.catalog;
  if (state.filterCollection) {
    source = source.filter(o => o.collection === state.filterCollection);
  }
  const groups = [...new Set(source.map(o => o.classification || o.groupLabel).filter(Boolean))].sort();

  sel.innerHTML = '<option value="">Alle Gruppen</option>';
  for (const g of groups) {
    const opt = document.createElement('option');
    opt.value = g;
    opt.textContent = g;
    sel.appendChild(opt);
  }

  // Restore selection if still valid, otherwise reset
  if (groups.includes(prev)) {
    sel.value = prev;
  } else {
    sel.value = '';
    state.filterGroup = '';
  }
}

/* ===== Viewer Rendering ===== */

function renderViewerMeta(obj) {
  const gamsUrl = GAMS_BASE + obj.pid;
  const meta = document.getElementById('viewerMeta');
  const v = obj.verification || {};

  // Marker summary
  const uncertain = v.uncertainCount || 0;
  const illegible = v.illegibleCount || 0;
  let markerHtml = '';
  if (uncertain > 0 || illegible > 0) {
    const parts = [];
    if (uncertain > 0) parts.push(`${uncertain}\u00d7[?]`);
    if (illegible > 0) parts.push(`${illegible}\u00d7[...]`);
    markerHtml = `<div class="viewer__meta-item">
      <span class="viewer__meta-label">Marker</span>
      <span class="badge badge-markers badge-markers-some">${parts.join(', ')}</span></div>`;
  }

  meta.innerHTML = `
    <div class="viewer__meta-item">
      <span class="viewer__meta-value viewer__meta-title">${escapeHtml(obj.titleClean || obj.label)}</span>
    </div>
    <div class="viewer__meta-item">
      <span class="viewer__meta-label">Sig.</span>
      <span class="viewer__meta-value">${escapeHtml(obj.signature)}</span>
    </div>
    <div class="viewer__meta-item">
      <a class="viewer__meta-link" href="${gamsUrl}" target="_blank" rel="noopener">${escapeHtml(obj.pid)}</a>
    </div>
    <div class="viewer__meta-item">
      <span class="viewer__meta-value">${COLLECTION_LABELS[obj.collection] || obj.collection}</span>
    </div>
    <div class="viewer__meta-item">
      <span class="viewer__meta-value">${escapeHtml(obj.classification || obj.groupLabel)}</span>
    </div>
    <div class="viewer__meta-item">
      <span class="viewer__meta-value">${escapeHtml(obj.lang)}</span>
    </div>
    <div class="viewer__meta-item">
      <span class="viewer__meta-label">VLM</span>
      <span class="badge badge-vlm" data-tooltip="VLM-Selbsteinschätzung (schwaches Signal)">${obj.confidence || '?'}</span>
    </div>
    ${markerHtml}
    ${obj.consensus ? (() => {
      const cat = obj.consensus.category || '';
      const catLabel = CONSENSUS_LABELS[cat] || cat.replace('consensus_', '');
      const cerPct = ((obj.consensus.effective_cer || 0) * 100).toFixed(1);
      const cls = 'badge-consensus-' + cat.replace('consensus_', '');
      return `<div class="viewer__meta-item">
        <span class="viewer__meta-label">Konsensus</span>
        <span class="badge badge-consensus ${cls}"
              data-tooltip="Cross-Model CER ${cerPct}%">${catLabel} \u00b7 ${cerPct}%</span>
      </div>`;
    })() : ''}
    <div class="viewer__meta-item">
      <span class="viewer__meta-label viewer__meta-model">${escapeHtml(obj.model)}</span>
    </div>
    ${obj.review ? `<div class="viewer__meta-item viewer__meta-review">
      <span class="badge-review badge-review-approved">Gepr\u00fcft</span>
      <span class="viewer__meta-value">von ${escapeHtml(obj.review.reviewed_by || '?')}${obj.review.reviewed_at ? ', ' + new Date(obj.review.reviewed_at).toLocaleDateString('de-AT') : ''}</span>
    </div>` : ''}`;
}

function renderViewerNav() {
  const obj = getViewerObject(state.currentObjectId);
  if (!obj) return;

  const pages = obj.pages || [];
  const total = pages.length;

  const qs = obj.quality_signals;
  const anomalies = qs?.page_length_anomalies || [];
  const isAnomaly = anomalies.includes(state.currentPage);
  const anomalyMark = isAnomaly ? ' <span class="viewer__page-anomaly" data-tooltip="Seitenlängen-Anomalie">\u26A0</span>' : '';

  // Page type badge for non-content pages
  const page = pages[state.currentPage];
  const pageType = page?.type || 'content';
  let typeBadge = '';
  if (pageType === 'blank') typeBadge = ' <span class="badge-page-type badge-page-blank">Leer</span>';
  else if (pageType === 'color_chart') typeBadge = ' <span class="badge-page-type badge-page-chart">Farbskala</span>';

  // Per-page consensus agreement dot
  let agreementDot = '';
  if (obj?.consensus?.pages) {
    const cp = obj.consensus.pages[state.currentPage];
    if (cp && cp.agreement) {
      const cerLabel = cp.cer !== null && cp.cer !== undefined ? ` CER ${(cp.cer * 100).toFixed(1)}%` : '';
      agreementDot = ` <span class="viewer__page-agreement agreement-${cp.agreement}" data-tooltip="${cp.agreement}${cerLabel}"></span>`;
    }
  }

  // Scan overview: use quality_signals for accurate counts (color_chart pages filtered from pages[])
  let scanInfo = '';
  const blankCount = qs?.blank_pages || pages.filter(p => p.type === 'blank').length;
  const chartCount = qs?.color_chart_pages || 0;
  const originalScans = total + chartCount;
  if (blankCount > 0 || chartCount > 0) {
    const parts = [];
    if (chartCount > 0) parts.push(`${originalScans} Scans`);
    if (blankCount > 0) parts.push(`${blankCount} leer`);
    if (chartCount > 0) parts.push(`${chartCount} Farbskala`);
    scanInfo = ` <span class="viewer__scan-info" data-tooltip="${parts.join(', ')}">(${parts.join(', ')})</span>`;
  }

  const pageInfoEl = document.getElementById('pageInfo');
  pageInfoEl.innerHTML = `<span class="viewer__page-info-text">${state.currentPage + 1} / ${total}${typeBadge}${agreementDot}${anomalyMark}${scanInfo}</span>`;
  pageInfoEl.style.cursor = total > 1 ? 'pointer' : '';
  document.getElementById('prevPageBtn').disabled = state.currentPage === 0;
  document.getElementById('nextPageBtn').disabled = state.currentPage >= total - 1;

  // Object navigation
  const idx = state.filteredObjects.findIndex(o => o.id === state.currentObjectId);
  document.getElementById('prevObjBtn').disabled = idx <= 0;
  document.getElementById('nextObjBtn').disabled = idx < 0 || idx >= state.filteredObjects.length - 1;
  document.getElementById('objInfo').textContent =
    idx >= 0 ? `Objekt ${idx + 1} / ${state.filteredObjects.length}` : '';
}

function activatePageJumpInput() {
  const obj = getViewerObject(state.currentObjectId);
  if (!obj) return;
  const total = (obj.pages || []).length;
  if (total <= 1) return;

  const el = document.getElementById('pageInfo');
  el.innerHTML = `<input type="number" class="viewer__page-jump" id="pageJumpInput"
    min="1" max="${total}" value="${state.currentPage + 1}" />`;

  const input = document.getElementById('pageJumpInput');
  input.focus();
  input.select();

  const ac = new AbortController();
  const restore = () => { ac.abort(); renderViewerNav(); };

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      ac.abort();
      const val = parseInt(input.value, 10);
      if (val >= 1 && val <= total && val - 1 !== state.currentPage) {
        state.currentPage = val - 1;
        history.replaceState(null, '', `#view/${state.currentObjectId}/${val}`);
        renderViewerPage();
        document.getElementById('imgPanel')?.scrollTo(0, 0);
        document.querySelector('.viewer__transcription-wrap')?.scrollTo(0, 0);
      } else {
        renderViewerNav();
      }
    }
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); restore(); }
  });
  input.addEventListener('blur', restore, { once: true, signal: ac.signal });
}

function renderViewerPage() {
  const obj = getViewerObject(state.currentObjectId);
  if (!obj) return;

  const pages = obj.pages || [];
  const page = pages[state.currentPage];

  // Reset image view on page change
  imgViewReset();

  // Image
  const img = document.getElementById('faksimile');
  const spinner = document.getElementById('imgSpinner');
  if (img && spinner) {
    const imgUrl = (obj.images && obj.images[state.currentPage]) || '';
    img.classList.remove('zoomed');
    img.style.display = 'none';
    spinner.style.display = '';

    if (imgUrl) {
      img.onload = () => { img.style.display = ''; spinner.style.display = 'none'; applyFitMode(); };
      img.onerror = () => {
        spinner.textContent = 'Bild konnte nicht geladen werden.';
        spinner.className = 'viewer__img-error';
      };
      img.src = imgUrl;
      img.alt = `${obj.titleClean || obj.label} — Seite ${state.currentPage + 1}`;
    } else {
      spinner.textContent = 'Kein Bild verfügbar.';
      spinner.className = 'viewer__img-error';
    }
  }

  // Transcription
  const key = editKey(state.currentObjectId, state.currentPage);
  const edited = state.editedTranscriptions.get(key);
  const transcriptionText = edited ? edited.transcription : (page ? page.transcription : '');
  const notesText = edited ? edited.notes : (page ? page.notes : '');

  if (state.editMode && state.isLocal) {
    renderEditMode(transcriptionText, notesText);
  } else {
    renderReadMode(transcriptionText, notesText, !!edited);
  }

  // Quality signals / confidence notes at bottom of text panel
  const bar = document.getElementById('verificationBar');
  if (bar) {
    let barHtml = '';
    const qs = obj.quality_signals;
    if (qs) {
      barHtml = renderQualitySignals(qs);
    }
    if (obj.confidenceNotes) {
      barHtml += `<div class="viewer__vlm-notes">${escapeHtml(obj.confidenceNotes)}</div>`;
    }
    bar.innerHTML = barHtml;
  }

  renderViewerNav();
  updateEditButtons();

  // Update diff or GT review if active
  if (state.diffMode) renderDiffView();
  if (state.gtReviewMode) renderGtReview();
}

function renderReadMode(transcription, notes, isEdited) {
  const wrap = document.querySelector('.viewer__transcription-wrap');
  if (!wrap) return;
  const label = isEdited ? '<span class="viewer__modified-label">bearbeitet</span> ' : '';
  wrap.innerHTML = `${label}<div class="viewer__transcription" id="transcription">${renderTranscription(transcription)}</div>`;

  const notesEl = document.getElementById('notes');
  if (notesEl) notesEl.innerHTML = notes ? renderTranscription(notes) : '';
}

function renderEditMode(transcription, notes) {
  const wrap = document.querySelector('.viewer__transcription-wrap');
  if (!wrap) return;
  wrap.innerHTML = '<textarea class="viewer__transcription-edit" id="transcriptionEdit"></textarea>';
  document.getElementById('transcriptionEdit').value = transcription || '';

  const notesEl = document.getElementById('notes');
  if (notesEl) {
    notesEl.innerHTML = '<textarea class="viewer__notes-edit" id="notesEdit"></textarea>';
    document.getElementById('notesEdit').value = notes || '';
  }
}

function saveCurrentEdit() {
  if (!state.editMode || !state.isLocal) return;
  const textarea = document.getElementById('transcriptionEdit');
  const notesArea = document.getElementById('notesEdit');
  if (!textarea) return;

  const obj = getViewerObject(state.currentObjectId);
  if (!obj) return;
  const page = (obj.pages || [])[state.currentPage];
  const origTranscription = page ? page.transcription : '';
  const origNotes = page ? page.notes : '';

  const newTranscription = textarea.value;
  const newNotes = notesArea ? notesArea.value : origNotes;

  const key = editKey(state.currentObjectId, state.currentPage);

  if (newTranscription !== origTranscription || newNotes !== origNotes) {
    state.editedTranscriptions.set(key, {
      transcription: newTranscription,
      notes: newNotes,
    });
  } else {
    // If reverted to original, remove the edit
    state.editedTranscriptions.delete(key);
  }

  saveEditsToStorage();
}

function updateEditButtons() {
  const editBtn = document.getElementById('editBtn');
  const jsonBtn = document.getElementById('saveBtn');
  const editSaveBtn = document.getElementById('editSaveBtn');
  const undoPageBtn = document.getElementById('editUndoPageBtn');
  const discardBtn = document.getElementById('discardBtn');
  const indicator = document.getElementById('editIndicator');
  const statusBar = document.getElementById('editStatus');

  const objCount = state.currentObjectId ? getEditCount(state.currentObjectId) : 0;
  const totalCount = state.editedTranscriptions.size;
  const hasPageEdit = state.currentObjectId
    ? state.editedTranscriptions.has(editKey(state.currentObjectId, state.currentPage))
    : false;

  if (!state.isLocal) {
    editBtn.disabled = true;
    editBtn.dataset.tooltip = 'Lokal starten für Edit-Modus: python -m http.server 8000';
    jsonBtn.disabled = true;
    jsonBtn.dataset.tooltip = 'Lokal starten für Export: python -m http.server 8000';
  } else {
    editBtn.disabled = false;
    editBtn.dataset.tooltip = state.editMode ? 'Zurück zur Leseansicht' : 'Transkription bearbeiten';
    jsonBtn.disabled = false;
    jsonBtn.dataset.tooltip = 'Korrekturen als JSON herunterladen';
  }

  editBtn.classList.toggle('active', state.editMode);
  indicator.classList.toggle('visible', objCount > 0);

  // Show save/undo only in edit mode
  editSaveBtn.style.display = state.editMode ? '' : 'none';
  undoPageBtn.style.display = state.editMode && hasPageEdit ? '' : 'none';
  discardBtn.style.display = objCount > 0 && state.isLocal ? '' : 'none';

  // Edit status bar
  if (statusBar) {
    if (objCount > 0) {
      const pageLabel = objCount === 1 ? 'Seite' : 'Seiten';
      statusBar.innerHTML = `
        <span class="viewer__edit-status-icon">&#9998;</span>
        <span class="viewer__edit-status-text">
          <strong>${objCount} ${pageLabel}</strong> bearbeitet an diesem Objekt${totalCount > objCount ? ` (${totalCount} gesamt)` : ''}
        </span>
        <span class="viewer__edit-status-storage">localStorage · bleibt im Browser</span>`;
      statusBar.style.display = '';
    } else {
      statusBar.style.display = 'none';
    }
  }

  // Diff button: show inline consensus status when available
  const diffBtn = document.getElementById('diffBtn');
  if (diffBtn) {
    const consensus = state.currentObjectId ? getConsensusData(state.currentObjectId) : null;
    const hasConsensus = consensus && consensus.pages && consensus.pages.length > 0;
    diffBtn.disabled = !hasConsensus;
    if (hasConsensus) {
      const cerPct = ((consensus.effective_cer || 0) * 100).toFixed(1);
      const agrPct = Math.round((1 - (consensus.effective_cer || 0)) * 100);
      const catShort = (consensus.category || '').replace('consensus_', '');
      diffBtn.innerHTML = `&#8700; Diff <span class="diff-btn__status diff-btn__status--${catShort}">${agrPct}%</span>`;
      diffBtn.dataset.tooltip = `Konsensus: ${CONSENSUS_LABELS[consensus.category] || catShort} \u00b7 CER ${cerPct}%`;
    } else {
      diffBtn.innerHTML = '&#8700; Diff';
      diffBtn.dataset.tooltip = 'Kein Konsensus-Vergleich verf\u00fcgbar';
    }
  }

  // GT Review button: show only when GT data exists and running locally
  const gtBtn = document.getElementById('reviewGtBtn');
  if (gtBtn) {
    const gt = state.currentObjectId ? getGtDraft(state.currentObjectId) : null;
    gtBtn.style.display = gt && state.isLocal ? '' : 'none';
    gtBtn.classList.toggle('gt-active', state.gtReviewMode);
  }
}

/* ===== Export ===== */

function buildExportJson(objectId) {
  const catalogObj = state.catalog.find(o => o.id === objectId);
  const fullObj = getViewerObject(objectId);
  if (!catalogObj || !fullObj) return null;

  const pages = (fullObj.pages || []).map((page, i) => {
    const key = editKey(objectId, i);
    const edited = state.editedTranscriptions.get(key);
    return {
      page: page.page || i + 1,
      transcription: edited ? edited.transcription : page.transcription,
      notes: edited ? edited.notes : page.notes,
      edited: !!edited,
    };
  });

  return {
    pid: catalogObj.pid,
    object_id: catalogObj.id.replace(/_gemini.*$/, ''),
    signature: catalogObj.signature,
    collection: catalogObj.collection,
    title: catalogObj.titleClean || catalogObj.title,
    model: catalogObj.model,
    pages,
    exported_at: new Date().toISOString(),
    source: 'szd-htr-viewer',
  };
}

function downloadJson(objectId) {
  const data = buildExportJson(objectId);
  if (!data) return;

  const filename = `${data.object_id}_${new Date().toISOString().slice(0, 16).replace(/[:.]/g, '-')}.json`;
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/* ===== Image Viewer (Zoom, Pan, Rotate) ===== */

const imgView = {
  scale: 1,
  rotation: 0,
  panX: 0,
  panY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  panStartX: 0,
  panStartY: 0,
  MIN_SCALE: 0.5,
  MAX_SCALE: 8,
  ZOOM_STEP: 1.25,
};

function imgViewReset() {
  imgView.scale = 1;
  imgView.rotation = 0;
  imgView.panX = 0;
  imgView.panY = 0;
  imgViewApply();
}

function imgViewApply() {
  const img = document.getElementById('faksimile');
  if (!img) return;
  img.style.transform = `translate(${imgView.panX}px, ${imgView.panY}px) scale(${imgView.scale}) rotate(${imgView.rotation}deg)`;
}

function imgViewZoom(delta, clientX, clientY) {
  const panel = document.getElementById('imgPanel');
  const img = document.getElementById('faksimile');
  if (!panel || !img) return;

  const oldScale = imgView.scale;
  const factor = delta > 0 ? imgView.ZOOM_STEP : 1 / imgView.ZOOM_STEP;
  imgView.scale = Math.min(imgView.MAX_SCALE, Math.max(imgView.MIN_SCALE, oldScale * factor));

  // Zoom toward cursor position
  if (clientX !== undefined && clientY !== undefined) {
    const rect = panel.getBoundingClientRect();
    const cx = clientX - rect.left;
    const cy = clientY - rect.top;
    const ratio = imgView.scale / oldScale;
    imgView.panX = cx - ratio * (cx - imgView.panX);
    imgView.panY = cy - ratio * (cy - imgView.panY);
  }

  imgViewApply();
}

function imgViewRotate() {
  imgView.rotation = (imgView.rotation + 90) % 360;
  imgViewApply();
}

function initImgViewEvents() {
  const panel = document.getElementById('imgPanel');
  if (!panel) return;

  // Scroll-wheel zoom
  panel.addEventListener('wheel', e => {
    e.preventDefault();
    imgViewZoom(e.deltaY < 0 ? 1 : -1, e.clientX, e.clientY);
  }, { passive: false });

  // Drag-to-pan
  panel.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    imgView.isDragging = true;
    imgView.dragStartX = e.clientX;
    imgView.dragStartY = e.clientY;
    imgView.panStartX = imgView.panX;
    imgView.panStartY = imgView.panY;
    panel.classList.add('dragging');
    e.preventDefault();
  });

  document.addEventListener('mousemove', e => {
    if (!imgView.isDragging) return;
    imgView.panX = imgView.panStartX + (e.clientX - imgView.dragStartX);
    imgView.panY = imgView.panStartY + (e.clientY - imgView.dragStartY);
    imgViewApply();
  });

  document.addEventListener('mouseup', () => {
    if (!imgView.isDragging) return;
    imgView.isDragging = false;
    const panel = document.getElementById('imgPanel');
    if (panel) panel.classList.remove('dragging');
  });

  // Touch pinch-zoom and drag
  let touchDist = 0;
  let touchMid = { x: 0, y: 0 };

  panel.addEventListener('touchstart', e => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      touchDist = Math.hypot(dx, dy);
      touchMid = {
        x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
        y: (e.touches[0].clientY + e.touches[1].clientY) / 2,
      };
    } else if (e.touches.length === 1 && imgView.scale > 1) {
      imgView.isDragging = true;
      imgView.dragStartX = e.touches[0].clientX;
      imgView.dragStartY = e.touches[0].clientY;
      imgView.panStartX = imgView.panX;
      imgView.panStartY = imgView.panY;
    }
  }, { passive: false });

  panel.addEventListener('touchmove', e => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const newDist = Math.hypot(dx, dy);
      if (touchDist > 0) {
        const ratio = newDist / touchDist;
        imgViewZoom(ratio > 1 ? 1 : -1, touchMid.x, touchMid.y);
        touchDist = newDist;
      }
    } else if (e.touches.length === 1 && imgView.isDragging) {
      imgView.panX = imgView.panStartX + (e.touches[0].clientX - imgView.dragStartX);
      imgView.panY = imgView.panStartY + (e.touches[0].clientY - imgView.dragStartY);
      imgViewApply();
    }
  }, { passive: false });

  panel.addEventListener('touchend', () => {
    imgView.isDragging = false;
    touchDist = 0;
  });
}

/* ===== Diff View (Cross-Model Verification) ===== */

// Word-level LCS diff
function diffWords(textA, textB) {
  const wordsA = (textA || '').split(/(\s+)/);
  const wordsB = (textB || '').split(/(\s+)/);

  // LCS on non-whitespace tokens
  const tokA = wordsA.filter(w => w.trim());
  const tokB = wordsB.filter(w => w.trim());

  const m = tokA.length;
  const n = tokB.length;

  // DP table for LCS
  const dp = Array.from({ length: m + 1 }, () => new Uint16Array(n + 1));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (tokA[i - 1] === tokB[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack
  const ops = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && tokA[i - 1] === tokB[j - 1]) {
      ops.unshift({ type: 'match', wordA: tokA[i - 1], wordB: tokB[j - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.unshift({ type: 'insert', wordB: tokB[j - 1] });
      j--;
    } else {
      ops.unshift({ type: 'delete', wordA: tokA[i - 1] });
      i--;
    }
  }

  return ops;
}

function computeDiffStats(ops) {
  let matches = 0, divergent = 0;
  for (const op of ops) {
    if (op.type === 'match') matches++;
    else divergent++;
  }
  const total = matches + divergent;
  const pct = total > 0 ? Math.round((matches / total) * 100) : 100;
  return { matches, divergent, total, agreementPct: pct };
}

function getConsensusData(objectId) {
  const obj = getViewerObject(objectId);
  return obj?.consensus || null;
}

function renderDiffView() {
  const diffPanel = document.getElementById('diffPanel');
  const diffContent = document.getElementById('diffContent');
  const diffStats = document.getElementById('diffStats');
  if (!diffPanel || !diffContent) return;

  const consensus = getConsensusData(state.currentObjectId);
  if (!consensus || !consensus.pages) {
    diffContent.innerHTML = '<div style="color:var(--sz-text-light);font-style:italic;padding:2rem">Kein Konsensus-Vergleich für dieses Objekt verfügbar.</div>';
    if (diffStats) diffStats.innerHTML = '';
    return;
  }

  const pageData = consensus.pages[state.currentPage];
  if (!pageData || pageData.agreement === 'skipped') {
    const reason = pageData?.agreement === 'skipped' ? 'Seite übersprungen (leer/Farbskala).' : 'Keine Daten für diese Seite.';
    diffContent.innerHTML = `<div style="color:var(--sz-text-light);font-style:italic;padding:2rem">${reason}</div>`;
    if (diffStats) diffStats.innerHTML = '';
    return;
  }

  const textA = pageData.transcription_a || '';
  const textB = pageData.transcription_b || '';

  if (!textA && !textB) {
    diffContent.innerHTML = '<div style="color:var(--sz-text-light);font-style:italic;padding:2rem">Keine Transkription auf dieser Seite.</div>';
    if (diffStats) diffStats.innerHTML = '';
    return;
  }

  const ops = diffWords(textA, textB);
  const stats = computeDiffStats(ops);

  // CER info for this page
  const cerInfo = pageData.cer !== null && pageData.cer !== undefined
    ? `<span>CER ${(pageData.cer * 100).toFixed(1)}%</span>` : '';
  const overallCer = consensus.effective_cer !== undefined
    ? `<span data-tooltip="Gesamt-CER über alle Seiten">Gesamt: ${(consensus.effective_cer * 100).toFixed(1)}%</span>` : '';

  diffStats.innerHTML = `
    <span class="diff__stats-agreement">${stats.agreementPct}% Übereinstimmung</span>
    <span>${stats.matches} gleich, <span class="diff__stats-divergent">${stats.divergent} abweichend</span></span>
    ${cerInfo}${overallCer}`;

  // Provider labels from consensus data
  const nameA = consensus.model_a || 'Modell A';
  const nameB = consensus.model_b || 'Modell B';

  // Build side-by-side columns
  let htmlA = '';
  let htmlB = '';

  for (const op of ops) {
    if (op.type === 'match') {
      const escaped = escapeHtml(op.wordA);
      htmlA += `<span class="diff__word diff__word--match">${escaped}</span> `;
      htmlB += `<span class="diff__word diff__word--match">${escaped}</span> `;
    } else if (op.type === 'delete') {
      htmlA += `<span class="diff__word diff__word--only-a" data-tooltip="Nur in A">${escapeHtml(op.wordA)}</span> `;
    } else if (op.type === 'insert') {
      htmlB += `<span class="diff__word diff__word--only-b" data-tooltip="Nur in B">${escapeHtml(op.wordB)}</span> `;
    }
  }

  diffContent.innerHTML = `
    <div class="diff__side-by-side">
      <div class="diff__column">
        <div class="diff__column-header">A — ${escapeHtml(nameA)}</div>
        ${htmlA}
      </div>
      <div class="diff__column">
        <div class="diff__column-header">B — ${escapeHtml(nameB)}</div>
        ${htmlB}
      </div>
    </div>
    <div class="diff__legend">
      <span class="diff__legend-item"><span class="diff__legend-swatch diff__legend-swatch--a"></span> Nur in A</span>
      <span class="diff__legend-item"><span class="diff__legend-swatch diff__legend-swatch--b"></span> Nur in B</span>
      <span class="diff__legend-item"><span class="diff__legend-swatch diff__legend-swatch--match"></span> Übereinstimmung</span>
    </div>`;
}

function toggleDiffMode() {
  // Exit edit mode if active
  if (state.editMode) {
    saveCurrentEdit();
    state.editMode = false;
    renderViewerPage();
    updateEditButtons();
  }

  if (state.diffMode) {
    resetDiffMode();
    return;
  }

  state.diffMode = true;
  // Hide only text panel; image panel stays visible
  document.getElementById('textPanel').style.display = 'none';
  document.getElementById('panelLabelRight').textContent = 'Diff (Cross-Model)';
  document.getElementById('diffPanel').style.display = '';
  document.getElementById('diffBtn').classList.add('active');

  // Update provider labels from consensus data
  const consensus = getConsensusData(state.currentObjectId);
  if (consensus) {
    const labelA = document.querySelector('.diff__provider-a');
    const labelB = document.querySelector('.diff__provider-b');
    if (labelA) labelA.textContent = `A: ${consensus.model_a || 'Modell A'}`;
    if (labelB) labelB.textContent = `B: ${consensus.model_b || 'Modell B'}`;
  }

  renderDiffView();
}

/* ===== GT Review Mode ===== */

async function loadGtData() {
  if (state.gtData) return state.gtData;
  try {
    const resp = await fetch('data/groundtruth.json');
    if (!resp.ok) return null;
    state.gtData = await resp.json();
    return state.gtData;
  } catch { return null; }
}

function getGtDraft(objectId) {
  if (!state.gtData) return null;
  return (state.gtData.objects || []).find(g => g.id === objectId);
}

function loadGtReviewsFromStorage() {
  if (!state.isLocal) return;
  try {
    const raw = localStorage.getItem(LS_GT_KEY);
    if (raw) {
      const entries = JSON.parse(raw);
      state.gtReviews = new Map(entries);
    }
  } catch { /* ignore */ }
}

function saveGtReviewsToStorage() {
  if (!state.isLocal) return;
  localStorage.setItem(LS_GT_KEY, JSON.stringify([...state.gtReviews]));
}

function toggleGtReview() {
  if (state.editMode) { saveCurrentEdit(); state.editMode = false; }
  if (state.diffMode) { resetDiffMode(); }

  state.gtReviewMode = !state.gtReviewMode;
  const btn = document.getElementById('reviewGtBtn');
  btn.classList.toggle('gt-active', state.gtReviewMode);

  if (state.gtReviewMode) {
    document.getElementById('textPanel').style.display = 'none';
    document.getElementById('panelLabelRight').textContent = 'GT Review';
    document.getElementById('diffPanel').style.display = '';
    renderGtReview();
  } else {
    document.getElementById('textPanel').style.display = '';
    document.getElementById('panelLabelRight').textContent = 'Transkription';
    document.getElementById('diffPanel').style.display = 'none';
    renderViewerPage();
  }
}

function renderGtReview() {
  const diffContent = document.getElementById('diffContent');
  const diffStats = document.getElementById('diffStats');
  if (!diffContent) return;

  const gt = getGtDraft(state.currentObjectId);
  if (!gt) {
    diffContent.innerHTML = '<p>Kein GT-Draft verfuegbar.</p>';
    diffStats.innerHTML = '';
    return;
  }

  const pageIdx = state.currentPage;
  const gtPage = (gt.pages || [])[pageIdx];
  if (!gtPage) {
    diffContent.innerHTML = '<p>Keine Daten fuer diese Seite.</p>';
    return;
  }

  const source = gtPage.source || 'unknown';
  const variants = gtPage.variants || {};
  const reviewKey = `${state.currentObjectId}:${pageIdx}`;
  const existingReview = state.gtReviews.get(reviewKey);

  // Source badge
  const sourceClass = source === 'consensus_3of3' ? 'gt-source--consensus'
    : source === 'majority_2of3' ? 'gt-source--majority'
    : source === 'skipped' ? 'gt-source--skipped'
    : 'gt-source--pro';
  const sourceLabel = source === 'consensus_3of3' ? '3/3 Konsensus'
    : source === 'majority_2of3' ? '2/3 Mehrheit'
    : source === 'skipped' ? 'Uebersprungen'
    : 'Pro only';

  // Stats
  const stats = gt.merge_stats || {};
  diffStats.innerHTML = `<span class="gt-review-panel__source ${sourceClass}">${sourceLabel}</span>
    <span style="font-size:0.72rem;margin-left:0.5rem">
      ${stats.consensus_3of3 || 0} Konsensus · ${stats.majority_2of3 || 0} Mehrheit · ${stats.pro_only || 0} Pro · ${stats.skipped || 0} Skip
    </span>`;

  if (source === 'skipped') {
    diffContent.innerHTML = `<div class="gt-review-panel">
      <p>Seite uebersprungen (${gtPage.type || 'blank'}): ${escapeHtml(gtPage.notes || '')}</p>
    </div>`;
    return;
  }

  // Current transcription (from review or from draft)
  const currentText = existingReview ? existingReview.transcription : gtPage.transcription;
  const isApproved = existingReview?.approved || false;

  // Build variant panels
  const variantEntries = [
    { key: 'pro', label: 'C: Gemini Pro', text: variants.pro || '' },
    { key: 'flash', label: 'B: Gemini Flash', text: variants.flash || '' },
    { key: 'flash_lite', label: 'A: Flash Lite', text: variants.flash_lite || '' },
  ];

  let variantsHtml = '';
  for (const v of variantEntries) {
    const isSelected = v.text === currentText;
    variantsHtml += `
      <div class="gt-variant ${isSelected ? 'selected' : ''}" data-variant="${v.key}">
        <div class="gt-variant__header">
          <span>${v.label}</span>
          <span>${v.text.length} Z.</span>
        </div>
        <div class="gt-variant__text">${escapeHtml(v.text || '(leer)')}</div>
      </div>`;
  }

  const approveLabel = isApproved ? '&#10003; Approved' : 'Approve Page';
  const approveClass = isApproved ? 'gt-approve-btn approved' : 'gt-approve-btn';

  diffContent.innerHTML = `
    <div class="gt-review-panel">
      <div style="font-size:0.75rem;color:var(--sz-text-light)">
        Klick auf eine Variante um sie als GT zu uebernehmen:
      </div>
      ${variantsHtml}
      <button type="button" class="${approveClass}" id="gtApproveBtn">${approveLabel}</button>
    </div>`;

  // Click handlers for variant selection
  diffContent.querySelectorAll('.gt-variant').forEach(el => {
    el.addEventListener('click', () => {
      const varKey = el.dataset.variant;
      const varText = variants[varKey] || '';
      // Save selection
      state.gtReviews.set(reviewKey, {
        transcription: varText,
        source: varKey,
        approved: false,
      });
      saveGtReviewsToStorage();
      renderGtReview();
    });
  });

  // Approve button
  const approveBtn = document.getElementById('gtApproveBtn');
  if (approveBtn) {
    approveBtn.addEventListener('click', () => {
      const review = state.gtReviews.get(reviewKey) || {
        transcription: gtPage.transcription,
        source: source,
      };
      review.approved = !review.approved;
      state.gtReviews.set(reviewKey, review);
      saveGtReviewsToStorage();
      renderGtReview();
      showToast(review.approved ? `Seite ${pageIdx + 1} approved` : `Seite ${pageIdx + 1} unapproved`);
    });
  }
}

function downloadGtReview(objectId) {
  const gt = getGtDraft(objectId);
  if (!gt) return;

  const reviewedPages = [];
  for (let i = 0; i < (gt.pages || []).length; i++) {
    const key = `${objectId}:${i}`;
    const review = state.gtReviews.get(key);
    const gtPage = gt.pages[i];
    reviewedPages.push({
      page: i + 1,
      transcription: review ? review.transcription : gtPage.transcription,
      type: gtPage.type || 'content',
      source: review ? review.source : gtPage.source,
      approved: review ? review.approved : false,
      expert_edited: !!review,
    });
  }

  const allApproved = reviewedPages.filter(p => p.type === 'content').every(p => p.approved);

  const output = {
    object_id: gt.object_id,
    collection: gt.collection,
    group: gt.group,
    title: gt.title,
    models: gt.models,
    pages: reviewedPages,
    expert_verified: allApproved,
    reviewed_by: 'Christopher Pollin',
    reviewed_at: new Date().toISOString(),
  };

  const blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${gt.object_id}_gt.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ===== Help View ===== */

function showHelp() {
  document.body.className = 'view-help';
  document.title = 'SZD-HTR \u2014 Hilfe';
  state.currentObjectId = null;
  state.editMode = false;
  resetDiffMode();
}

/* ===== Event Handlers ===== */

function initEvents() {
  // Search
  const searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('input', debounce(() => {
    state.searchQuery = searchInput.value.trim();
    state.catalogPage = 0;
    renderCatalog();
  }, SEARCH_DEBOUNCE_MS));

  // Filters
  document.getElementById('filterCollection').addEventListener('change', e => {
    state.filterCollection = e.target.value;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('filterGroup').addEventListener('change', e => {
    state.filterGroup = e.target.value;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('filterConfidence').addEventListener('change', e => {
    state.filterConfidence = e.target.value;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('filterReviewStatus').addEventListener('change', e => {
    state.filterReviewStatus = e.target.value;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('filterConsensus').addEventListener('change', e => {
    state.filterConsensus = e.target.value;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('clearFilters').addEventListener('click', () => {
    state.searchQuery = '';
    state.filterCollection = '';
    state.filterGroup = '';
    state.filterConfidence = '';
    state.filterReviewStatus = '';
    state.filterConsensus = '';
    state.catalogPage = 0;
    restoreFilterUI();
    renderCatalog();
  });

  // Sort
  document.querySelectorAll('.catalog__table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const field = th.dataset.sort;
      if (state.sortField === field) {
        state.sortAsc = !state.sortAsc;
      } else {
        state.sortField = field;
        state.sortAsc = true;
      }
      state.catalogPage = 0;
      renderCatalog();
    });
  });

  // Table row click + keyboard
  const catalogBody = document.getElementById('catalogBody');
  catalogBody.addEventListener('click', e => {
    const row = e.target.closest('tr[data-id]');
    if (row) navigate('view/' + row.dataset.id);
  });
  catalogBody.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      const row = e.target.closest('tr[data-id]');
      if (row) { e.preventDefault(); navigate('view/' + row.dataset.id); }
    }
  });

  // Pagination
  document.getElementById('prevPage').addEventListener('click', () => {
    if (state.catalogPage > 0) { state.catalogPage--; renderCatalog(); }
  });
  document.getElementById('nextPage').addEventListener('click', () => {
    state.catalogPage++;
    renderCatalog();
  });

  // Back to catalog
  document.getElementById('backBtn').addEventListener('click', e => {
    e.preventDefault();
    navigate(buildCatalogHash());
  });

  // Viewer: page nav
  document.getElementById('prevPageBtn').addEventListener('click', () => changeViewerPage(-1));
  document.getElementById('nextPageBtn').addEventListener('click', () => changeViewerPage(1));
  document.getElementById('pageInfo').addEventListener('click', activatePageJumpInput);

  // Viewer: object nav
  document.getElementById('prevObjBtn').addEventListener('click', () => changeViewerObject(-1));
  document.getElementById('nextObjBtn').addEventListener('click', () => changeViewerObject(1));

  // Viewer: image controls (all in nav bar)
  document.getElementById('navZoomInBtn').addEventListener('click', () => imgViewZoom(1));
  document.getElementById('navZoomOutBtn').addEventListener('click', () => imgViewZoom(-1));
  document.getElementById('navRotateBtn').addEventListener('click', imgViewRotate);
  document.getElementById('navResetBtn').addEventListener('click', imgViewReset);
  document.getElementById('navFitBtn').addEventListener('click', toggleFitMode);
  initImgViewEvents();

  // Viewer: diff
  document.getElementById('diffBtn').addEventListener('click', toggleDiffMode);

  // Viewer: GT review
  document.getElementById('reviewGtBtn').addEventListener('click', toggleGtReview);

  // Viewer: edit toggle
  document.getElementById('editBtn').addEventListener('click', () => {
    if (!state.isLocal) return;
    if (state.diffMode) toggleDiffMode();
    if (state.editMode) saveCurrentEdit();
    state.editMode = !state.editMode;
    renderViewerPage();
  });

  // Viewer: explicit save (in edit mode)
  document.getElementById('editSaveBtn').addEventListener('click', () => {
    if (!state.editMode || !state.isLocal) return;
    saveCurrentEdit();
    showToast('Gespeichert (localStorage)');
    updateEditButtons();
  });

  // Viewer: undo current page
  document.getElementById('editUndoPageBtn').addEventListener('click', () => {
    if (!state.currentObjectId) return;
    const key = editKey(state.currentObjectId, state.currentPage);
    if (state.editedTranscriptions.has(key)) {
      state.editedTranscriptions.delete(key);
      saveEditsToStorage();
      renderViewerPage();
      showToast(`Seite ${state.currentPage + 1} zurückgesetzt`);
    }
  });

  // Viewer: JSON download
  document.getElementById('saveBtn').addEventListener('click', () => {
    if (!state.isLocal || !state.currentObjectId) return;
    if (state.gtReviewMode) {
      downloadGtReview(state.currentObjectId);
      showToast('GT Review exportiert');
      return;
    }
    if (state.editMode) saveCurrentEdit();
    downloadJson(state.currentObjectId);
    showToast('JSON exportiert');
  });

  // Viewer: discard all edits for this object
  document.getElementById('discardBtn').addEventListener('click', () => {
    if (!state.currentObjectId) return;
    const count = getEditCount(state.currentObjectId);
    if (count === 0) return;
    for (const key of [...state.editedTranscriptions.keys()]) {
      if (key.startsWith(state.currentObjectId + ':')) {
        state.editedTranscriptions.delete(key);
      }
    }
    saveEditsToStorage();
    state.editMode = false;
    renderViewerPage();
    showToast(`${count} Seite(n) zurückgesetzt`);
  });

  // Keyboard
  document.addEventListener('keydown', e => {
    // Ctrl+S / Cmd+S to save in edit mode (works even in textareas)
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      if (state.editMode && state.isLocal) {
        saveCurrentEdit();
        showToast('Gespeichert (localStorage)');
        updateEditButtons();
      }
      return;
    }

    // Don't capture when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

    if (document.body.classList.contains('view-viewer')) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); changeViewerPage(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); changeViewerPage(1); }
      if (e.key === '+' || e.key === '=') { e.preventDefault(); imgViewZoom(1); }
      if (e.key === '-') { e.preventDefault(); imgViewZoom(-1); }
      if (e.key === '0') { e.preventDefault(); imgViewReset(); }
      if (e.key === 'r' || e.key === 'R') { e.preventDefault(); imgViewRotate(); }
      if (e.key === 'Escape') {
        if (state.editMode) {
          saveCurrentEdit();
          state.editMode = false;
          renderViewerPage();
        } else {
          navigate(buildCatalogHash());
        }
      }
    }

    // Escape from knowledge/about views
    if (document.body.classList.contains('view-knowledge-doc') && e.key === 'Escape') {
      navigate('knowledge');
    }
    if (document.body.classList.contains('view-knowledge') && e.key === 'Escape') {
      navigate(buildCatalogHash());
    }
    if (document.body.classList.contains('view-about') && e.key === 'Escape') {
      navigate(buildCatalogHash());
    }
    if (document.body.classList.contains('view-help') && e.key === 'Escape') {
      navigate(buildCatalogHash());
    }
  });

  // Touch swipe
  let touchStartX = 0;
  document.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', e => {
    if (!document.body.classList.contains('view-viewer')) return;
    if (e.target.tagName === 'TEXTAREA') return;
    const diff = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(diff) > 60) changeViewerPage(diff < 0 ? 1 : -1);
  });

  // Hash change
  window.addEventListener('hashchange', route);

}

function changeViewerPage(delta) {
  if (state.editMode) saveCurrentEdit();
  const obj = getViewerObject(state.currentObjectId);
  if (!obj) return;
  const next = state.currentPage + delta;
  if (next >= 0 && next < (obj.pages || []).length) {
    state.currentPage = next;
    // Update hash without full re-render
    history.replaceState(null, '', `#view/${state.currentObjectId}/${state.currentPage + 1}`);
    renderViewerPage();
    document.getElementById('imgPanel')?.scrollTo(0, 0);
    document.querySelector('.viewer__transcription-wrap')?.scrollTo(0, 0);
  }
}

function changeViewerObject(delta) {
  if (state.editMode) saveCurrentEdit();
  const idx = state.filteredObjects.findIndex(o => o.id === state.currentObjectId);
  const next = idx + delta;
  if (next >= 0 && next < state.filteredObjects.length) {
    navigate('view/' + state.filteredObjects[next].id);
  }
}

/* ===== Init ===== */

async function init() {
  detectLocal();
  loadFitMode();
  applyFitMode();
  loadEditsFromStorage();
  loadGtReviewsFromStorage();

  try {
    await loadCatalog();
  } catch {
    document.getElementById('catalog').innerHTML =
      '<div class="loading" style="animation:none">Fehler beim Laden des Katalogs.</div>';
    return;
  }

  // Load GT data in background
  loadGtData();

  state.hasReviewData = state.catalog.some(o => o.needsReview !== undefined);
  state.hasConsensusData = state.catalog.some(o => o.consensusCategory);
  initCatalogFilters();
  renderStats();
  applyFilters();
  initEvents();
  route();
}

init();
