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
  filterReview: false,
  editMode: false,
  diffMode: false,
  editedTranscriptions: new Map(),
  isLocal: false,
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
  if (!hash || hash === 'help') return { view: 'catalog', objectId: null, page: 0 };
  const m = hash.match(/^view\/(.+?)(?:\/(\d+))?$/);
  if (m) return { view: 'viewer', objectId: m[1], page: m[2] ? parseInt(m[2], 10) - 1 : 0 };
  return { view: 'catalog', objectId: null, page: 0 };
}

function navigate(hash) {
  if (location.hash === '#' + hash || (!location.hash && !hash)) return;
  location.hash = hash;
}

function route() {
  const r = parseHash();
  if (r.view === 'viewer' && r.objectId) {
    showViewer(r.objectId, r.page);
  } else {
    showCatalog();
  }
  // Help modal
  if (location.hash === '#help') openHelp();
}

function resetDiffMode() {
  if (!state.diffMode) return;
  state.diffMode = false;
  const el = id => document.getElementById(id);
  el('diffPanel') && (el('diffPanel').style.display = 'none');
  el('textPanel') && (el('textPanel').style.display = '');
  const lr = el('panelLabelRight');
  if (lr) lr.textContent = 'Transkription';
  const db = el('diffBtn');
  if (db) db.classList.remove('active');
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

  renderViewerMeta(catalogObj);
  renderViewerNav();
  renderViewerPage();
  updateEditButtons();
  requestAnimationFrame(() => document.getElementById('viewerMeta')?.focus());
}

/* ===== Review / Quality Signals ===== */

function renderReviewCell(obj) {
  if (obj.needsReview === undefined) return '';
  if (obj.needsReview) {
    const reasons = (obj.needsReviewReasons || []).join(', ') || 'Review empfohlen';
    return `<span class="badge-review badge-review-yes" data-tooltip="${escapeHtml(reasons)}">Review</span>`;
  }
  return '<span class="badge-review badge-review-ok" data-tooltip="Keine Auffälligkeiten">OK</span>';
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
        <span class="badge-review badge-review-ok">OK</span></div>`);
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

function renderQualityCell(v, confidence) {
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

  return markerHtml + vlmHtml;
}

/* ===== Stats Dashboard ===== */

function renderStats() {
  const el = document.getElementById('catalogStats');
  if (!el || state.catalog.length === 0) return;

  const total = state.catalog.length;

  // Count per collection
  const perCol = {};
  for (const col of state.collections) perCol[col] = 0;
  const perGroup = {};
  let reviewCount = 0;
  const hasReview = state.catalog.some(o => o.needsReview !== undefined);

  for (const o of state.catalog) {
    perCol[o.collection] = (perCol[o.collection] || 0) + 1;
    const g = o.classification || o.groupLabel || '?';
    perGroup[g] = (perGroup[g] || 0) + 1;
    if (o.needsReview) reviewCount++;
  }

  // Summary line: chips for collections
  const colChips = state.collections.map(c => {
    const label = COLLECTION_LABELS[c] || c;
    return `<span class="catalog__stats-chip"><strong>${perCol[c]}</strong> ${escapeHtml(label)}</span>`;
  }).join('');

  const reviewChip = hasReview
    ? `<span class="catalog__stats-chip ${reviewCount > 0 ? 'catalog__stats-chip--review-warn' : 'catalog__stats-chip--review-ok'}"><strong>${reviewCount}</strong> Review</span>`
    : '';

  // Detail section: groups
  const groupEntries = Object.entries(perGroup).sort((a, b) => b[1] - a[1]);
  const groupItems = groupEntries.map(([g, n]) =>
    `<span class="catalog__stats-bar-item"><strong>${n}</strong> ${escapeHtml(g)}</span>`
  ).join('');

  el.innerHTML = `
    <div class="catalog__stats-summary">
      <span class="catalog__stats-total">${total} Objekte</span>
      <div class="catalog__stats-chips">${colChips}${reviewChip}</div>
      <button type="button" class="catalog__stats-toggle" id="statsToggle" aria-expanded="false">Details &#9662;</button>
    </div>
    <div class="catalog__stats-details" id="statsDetails">
      <div class="catalog__stats-section">
        <div class="catalog__stats-section-label">Nach Typ</div>
        <div class="catalog__stats-bar">${groupItems}</div>
      </div>
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
  if (state.filterReview) {
    list = list.filter(o => o.needsReview);
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
      const qualityHtml = renderQualityCell(v, obj.confidence);
      const titleFull = escapeHtml(obj.titleClean || obj.label);
      html += `<tr data-id="${obj.id}" tabindex="0">
        <td class="col-thumb"><img src="${obj.thumbnail || ''}" loading="lazy" alt="" onerror="this.style.display='none'"></td>
        <td class="col-title" data-tooltip="${escapeHtml(obj.title)}">${titleFull}</td>
        <td class="col-sig">${escapeHtml(obj.signature)}</td>
        <td class="col-pid">${escapeHtml(obj.pid)}</td>
        <td class="col-collection">${COLLECTION_LABELS[obj.collection] || obj.collection}</td>
        <td class="col-group" data-tooltip="${escapeHtml(obj.objecttyp || '')}">${escapeHtml(obj.classification || obj.groupLabel)}</td>
        <td class="col-lang">${escapeHtml(obj.lang)}</td>
        <td class="col-review">${renderReviewCell(obj)}</td>
        <td class="col-quality">${qualityHtml}</td>
        <td class="col-pages" data-tooltip="Seitenanzahl">${obj.pageCount || '—'}</td>
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

  // Show review filter only if data has needsReview
  const hasReviewData = state.catalog.some(o => o.needsReview !== undefined);
  document.getElementById('filterReviewLabel').style.display = hasReviewData ? '' : 'none';

  // Show/hide clear button
  const hasFilters = state.searchQuery || state.filterCollection || state.filterGroup || state.filterConfidence || state.filterReview;
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
    <div class="viewer__meta-item">
      <span class="viewer__meta-label viewer__meta-model">${escapeHtml(obj.model)}</span>
    </div>`;
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
  document.getElementById('pageInfo').innerHTML = `${state.currentPage + 1} / ${total}${anomalyMark}`;
  document.getElementById('prevPageBtn').disabled = state.currentPage === 0;
  document.getElementById('nextPageBtn').disabled = state.currentPage >= total - 1;

  // Object navigation
  const idx = state.filteredObjects.findIndex(o => o.id === state.currentObjectId);
  document.getElementById('prevObjBtn').disabled = idx <= 0;
  document.getElementById('nextObjBtn').disabled = idx < 0 || idx >= state.filteredObjects.length - 1;
  document.getElementById('objInfo').textContent =
    idx >= 0 ? `Objekt ${idx + 1} / ${state.filteredObjects.length}` : '';
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
      img.onload = () => { img.style.display = ''; spinner.style.display = 'none'; };
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

  // Update diff if active
  if (state.diffMode) renderDiffView();
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

// Placeholder data for prototype
const DIFF_PLACEHOLDER = {
  objectId: 'korrespondenz_fleischer_gemini-3.1-flash-lite-preview',
  providerA: { name: 'Gemini Flash Lite', model: 'gemini-3.1-flash-lite-preview' },
  providerB: { name: 'Claude Sonnet', model: 'claude-sonnet-4-20250514' },
  pages: [
    {
      page: 1,
      textA: 'Wien, den 22. Mai 1901.\n\nLieber Max!\n\nIch danke Dir herzlich für Deinen lieben Brief, den ich soeben erhalte. Es freut mich außerordentlich, daß Du mit Deinem neuen Aufenthalt zufrieden bist und daß es Dir gesundheitlich besser geht.',
      textB: 'Wien, den 22. Mai 1901.\n\nLieber Max!\n\nIch danke Dir herzlichst für Deinen lieben Brief, den ich soeben erhalten habe. Es freut mich außerordentlich, daß Du mit Deinem neuen Aufenthalte zufrieden bist und daß es Dir gesundheitlich besser geht.',
    },
    {
      page: 2,
      textA: 'Was meine literarischen Pläne betrifft, so arbeite ich jetzt an einer Novelle, die mich sehr beschäftigt. Ich hoffe, sie bis zum Herbst [?] fertigzustellen.\n\nMit herzlichen Grüßen\nDein Stefan',
      textB: 'Was meine litterarischen Pläne betrifft, so arbeite ich jetzt an einer Novelle, die mich sehr beschäftigt. Ich hoffe, sie bis zum Herbste fertigzustellen.\n\nMit herzlichen Grüßen\nDein Stefan',
    },
    {
      page: 3,
      textA: '',
      textB: '',
    },
  ],
};

function renderDiffView() {
  const diffPanel = document.getElementById('diffPanel');
  const diffContent = document.getElementById('diffContent');
  const diffStats = document.getElementById('diffStats');
  if (!diffPanel || !diffContent) return;

  const pageData = DIFF_PLACEHOLDER.pages[state.currentPage];
  if (!pageData || (!pageData.textA && !pageData.textB)) {
    diffContent.innerHTML = '<div style="color:var(--sz-text-light);font-style:italic;padding:2rem">Keine Transkription auf dieser Seite.</div>';
    diffStats.innerHTML = '';
    return;
  }

  const ops = diffWords(pageData.textA, pageData.textB);
  const stats = computeDiffStats(ops);

  // Stats
  diffStats.innerHTML = `
    <span class="diff__stats-agreement">${stats.agreementPct}% Übereinstimmung</span>
    <span>${stats.matches} gleich, <span class="diff__stats-divergent">${stats.divergent} abweichend</span></span>
    <span class="diff__prototype-badge">Prototyp — Platzhalterdaten</span>`;

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
        <div class="diff__column-header">A — ${escapeHtml(DIFF_PLACEHOLDER.providerA.name)}</div>
        ${htmlA}
      </div>
      <div class="diff__column">
        <div class="diff__column-header">B — ${escapeHtml(DIFF_PLACEHOLDER.providerB.name)}</div>
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
  renderDiffView();
}

/* ===== Help Modal ===== */

function openHelp() {
  document.getElementById('helpOverlay').classList.add('open');
}

function closeHelp() {
  document.getElementById('helpOverlay').classList.remove('open');
  if (location.hash === '#help') history.replaceState(null, '', '#');
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

  document.getElementById('filterReview').addEventListener('change', e => {
    state.filterReview = e.target.checked;
    state.catalogPage = 0;
    renderCatalog();
  });

  document.getElementById('clearFilters').addEventListener('click', () => {
    state.searchQuery = '';
    state.filterCollection = '';
    state.filterGroup = '';
    state.filterConfidence = '';
    state.filterReview = false;
    searchInput.value = '';
    document.getElementById('filterCollection').value = '';
    document.getElementById('filterGroup').value = '';
    document.getElementById('filterConfidence').value = '';
    document.getElementById('filterReview').checked = false;
    state.catalogPage = 0;
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
    navigate('');
  });

  // Viewer: page nav
  document.getElementById('prevPageBtn').addEventListener('click', () => changeViewerPage(-1));
  document.getElementById('nextPageBtn').addEventListener('click', () => changeViewerPage(1));

  // Viewer: object nav
  document.getElementById('prevObjBtn').addEventListener('click', () => changeViewerObject(-1));
  document.getElementById('nextObjBtn').addEventListener('click', () => changeViewerObject(1));

  // Viewer: image controls
  document.getElementById('zoomInBtn').addEventListener('click', () => imgViewZoom(1));
  document.getElementById('zoomOutBtn').addEventListener('click', () => imgViewZoom(-1));
  document.getElementById('zoomResetBtn').addEventListener('click', imgViewReset);
  document.getElementById('rotateBtn').addEventListener('click', imgViewRotate);
  initImgViewEvents();

  // Viewer: diff
  document.getElementById('diffBtn').addEventListener('click', toggleDiffMode);

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
          navigate('');
        }
      }
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

  // Help
  document.getElementById('helpBtn').addEventListener('click', () => {
    navigate('help');
    openHelp();
  });
  document.getElementById('helpClose').addEventListener('click', closeHelp);
  document.getElementById('helpOverlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeHelp();
  });
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
  loadEditsFromStorage();

  try {
    await loadCatalog();
  } catch {
    document.getElementById('catalog').innerHTML =
      '<div class="loading" style="animation:none">Fehler beim Laden des Katalogs.</div>';
    return;
  }

  initCatalogFilters();
  renderStats();
  applyFilters();
  renderCatalog();
  initEvents();
  route();
}

init();
