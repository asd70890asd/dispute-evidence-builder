const API_BASE = 'http://127.0.0.1:8000/api';

// DOM Elements
const els = {
    emptyState: document.getElementById('empty-state'),
    colMaterials: document.getElementById('col-materials'),
    colTimeline: document.getElementById('col-timeline'),
    colClaims: document.getElementById('col-claims'),
    materialsList: document.getElementById('materials-list'),
    timelineList: document.getElementById('timeline-list'),
    claimsList: document.getElementById('claims-list'),
    materialsCount: document.getElementById('materials-count'),
    gapsPanel: document.getElementById('gaps-panel'),
    gapsContent: document.getElementById('gaps-content'),
    inconsistenciesPanel: document.getElementById('inconsistencies-panel'),
    inconsistenciesContent: document.getElementById('inconsistencies-content'),
    uploadForm: document.getElementById('upload-form'),
    claimForm: document.getElementById('claim-form'),
    btnLoadSample: document.getElementById('btn-load-sample'),
    btnReset: document.getElementById('btn-reset'),
    btnExport: document.getElementById('btn-export'),
    modal: document.getElementById('detail-modal'),
    modalClose: document.getElementById('modal-close')
};

// Event Listeners
els.uploadForm.addEventListener('submit', handleUpload);
els.claimForm.addEventListener('submit', handleAddClaim);
els.btnLoadSample.addEventListener('click', loadSampleCase);
els.btnReset.addEventListener('click', resetCase);
els.btnExport.addEventListener('click', () => window.open(`${API_BASE}/report`, '_blank'));
els.modalClose.addEventListener('click', () => els.modal.close());

// Initial Load
loadAllData();

async function loadAllData() {
    try {
        const [materialsRes, timelineRes, claimsRes, gapsRes, inconsistenciesRes] = await Promise.all([
            fetch(`${API_BASE}/materials`),
            fetch(`${API_BASE}/timeline`),
            fetch(`${API_BASE}/claims`),
            fetch(`${API_BASE}/gaps`),
            fetch(`${API_BASE}/inconsistencies`)
        ]);

        const materials = await materialsRes.json();
        const timeline = await timelineRes.json();
        const claims = await claimsRes.json();
        const gaps = await gapsRes.json();
        const inconsistencies = await inconsistenciesRes.json();

        updateVisibility(materials.length > 0);

        renderMaterials(materials);
        renderTimeline(timeline);
        renderClaims(claims);
        renderGaps(gaps);
        renderInconsistencies(inconsistencies);
    } catch (err) {
        console.error("Failed to load data:", err);
    }
}

function updateVisibility(hasData) {
    if (hasData) {
        els.emptyState.classList.add('hidden');
        els.colMaterials.classList.remove('hidden');
        els.colTimeline.classList.remove('hidden');
        els.colClaims.classList.remove('hidden');
    } else {
        els.emptyState.classList.remove('hidden');
        els.colMaterials.classList.add('hidden');
        els.colTimeline.classList.add('hidden');
        els.colClaims.classList.add('hidden');
    }
}

function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Render Functions
function renderMaterials(materials) {
    els.materialsCount.textContent = materials.length;
    els.materialsList.innerHTML = '';

    materials.forEach(mat => {
        const dateDisplay = mat.date ? escapeHtml(mat.date) : '<span class="date-unknown">date unknown — set manually</span>';
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-header">
                <span class="card-title">${escapeHtml(mat.filename)}</span>
                <span class="kind-badge kind-${escapeHtml(mat.kind)}">${escapeHtml(mat.kind).replace('_', ' ')}</span>
            </div>
            <div class="card-meta">Date: ${dateDisplay}</div>
            <div class="card-desc">${mat.description ? escapeHtml(mat.description) : '<em>No description</em>'}</div>
            <div class="edit-actions">
                <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" data-action="edit" data-id="${mat.id}">Edit</button>
                <button class="btn btn-danger" data-action="del-mat" data-id="${mat.id}">Delete</button>
            </div>
            <form id="edit-form-${mat.id}" class="edit-form hidden" data-edit-form="${mat.id}">
                <input type="date" id="edit-date-${mat.id}" value="${mat.date || ''}" style="padding:4px; font-size:0.875rem;">
                <textarea id="edit-desc-${mat.id}" rows="2" placeholder="Description...">${escapeHtml(mat.description || '')}</textarea>
                <div class="edit-actions">
                    <button type="submit" class="btn btn-primary" style="padding: 4px 8px; font-size: 0.75rem;">Save</button>
                    <button type="button" class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" data-action="edit" data-id="${mat.id}">Cancel</button>
                </div>
            </form>
        `;
        els.materialsList.appendChild(card);
    });
}

function renderTimeline(timeline) {
    els.timelineList.innerHTML = '';

    timeline.forEach(item => {
        const dotColor = getKindColor(item.kind);
        const dateStr = item.date ? escapeHtml(item.date) : 'Undated';
        const el = document.createElement('div');
        el.className = 'timeline-item';
        el.innerHTML = `
            <div class="timeline-dot" style="background: ${dotColor};"></div>
            <div class="timeline-content">
                <div class="timeline-date">${dateStr}</div>
                <div style="font-size: 0.875rem; font-weight: 500; margin-bottom: 4px;">${escapeHtml(item.filename)}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${item.description ? escapeHtml(item.description) : 'No description'}</div>
            </div>
        `;
        el.addEventListener('click', () => openModal(item));
        els.timelineList.appendChild(el);
    });
}

function renderClaims(claims) {
    els.claimsList.innerHTML = '';

    claims.forEach(claim => {
        const card = document.createElement('div');
        card.className = 'card';

        let matchesHtml = '';
        if (claim.matches && claim.matches.length > 0) {
            matchesHtml = '<div class="matches-list">';
            claim.matches.forEach(m => {
                matchesHtml += `
                    <div class="match-item">
                        <span class="match-score">Score: ${Number(m.score).toFixed(3)}</span> -
                        <strong>${escapeHtml(m.filename)}</strong> (${m.date ? escapeHtml(m.date) : 'Undated'})<br>
                        ${escapeHtml(m.description_summary || '')}
                    </div>
                `;
            });
            matchesHtml += '</div>';
        } else {
            matchesHtml = '<div class="matches-list" style="color:var(--text-muted);">No matching evidence found.</div>';
        }

        card.innerHTML = `
            <div class="card-header">
                <div style="font-size: 0.875rem; font-weight: 600;">${escapeHtml(claim.text)}</div>
                <button class="btn btn-danger" style="margin-left:8px;" data-action="del-claim" data-id="${claim.id}">&times;</button>
            </div>
            <span class="status-badge status-${escapeHtml(claim.status)}">${escapeHtml(claim.status).replace('_', ' ').toUpperCase()}</span>
            ${matchesHtml}
        `;
        els.claimsList.appendChild(card);
    });
}

function renderGaps(gaps) {
    const hasGaps = gaps.unsupported_claims.length > 0 || gaps.undated_materials.length > 0;
    if (hasGaps) {
        els.gapsPanel.classList.remove('hidden');
        let html = '<ul class="analysis-list">';
        gaps.unsupported_claims.forEach(c => {
            html += `<li><strong>Unsupported Claim:</strong> &quot;${escapeHtml(c.text)}&quot;</li>`;
        });
        gaps.undated_materials.forEach(m => {
            html += `<li><strong>Undated Material:</strong> ${escapeHtml(m.filename)} requires a date for the timeline.</li>`;
        });
        html += '</ul>';
        els.gapsContent.innerHTML = html;
    } else {
        els.gapsPanel.classList.add('hidden');
    }
}

function renderInconsistencies(inconsistencies) {
    if (inconsistencies && inconsistencies.length > 0) {
        els.inconsistenciesPanel.classList.remove('hidden');
        let html = '<ul class="analysis-list">';
        inconsistencies.forEach(inc => {
            html += `<li>${escapeHtml(inc.note)} (Involves ${inc.material_ids.length} materials)</li>`;
        });
        html += '</ul>';
        els.inconsistenciesContent.innerHTML = html;
    } else {
        els.inconsistenciesPanel.classList.add('hidden');
    }
}

// Handlers & API Calls
async function handleUpload(e) {
    e.preventDefault();
    const formData = new FormData(els.uploadForm);

    try {
        const res = await fetch(`${API_BASE}/materials/upload`, {
            method: 'POST',
            body: formData
        });
        if (!res.ok) {
            const errBody = await res.json().catch(() => ({}));
            throw new Error(errBody.detail || 'Upload failed');
        }
        els.uploadForm.reset();
        await loadAllData();
    } catch (err) {
        alert(err.message);
    }
}

async function handleAddClaim(e) {
    e.preventDefault();
    const input = document.getElementById('claim-text');
    const text = input.value.trim();
    if (!text) return;

    try {
        const res = await fetch(`${API_BASE}/claims`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (!res.ok) throw new Error('Failed to add claim.');
        input.value = '';
        await loadAllData();
    } catch (err) {
        alert(err.message);
    }
}

async function loadSampleCase() {
    try {
        await fetch(`${API_BASE}/case/sample`, { method: 'POST' });
    } finally {
        await loadAllData();
    }
}

async function resetCase() {
    await fetch(`${API_BASE}/case/reset`, { method: 'POST' });
    await loadAllData();
}

async function deleteMaterial(id) {
    if (!confirm("Delete this material?")) return;
    await fetch(`${API_BASE}/materials/${id}`, { method: 'DELETE' });
    await loadAllData();
}

async function deleteClaim(id) {
    await fetch(`${API_BASE}/claims/${id}`, { method: 'DELETE' });
    await loadAllData();
}

async function saveMaterial(e, id) {
    e.preventDefault();
    const date = document.getElementById(`edit-date-${id}`).value;
    const description = document.getElementById(`edit-desc-${id}`).value;

    await fetch(`${API_BASE}/materials/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: date || null, description })
    });
    await loadAllData();
}

// Delegated clicks (replaces inline onclick handlers)
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.getAttribute('data-action');
    const id = btn.getAttribute('data-id');
    if (action === 'edit') {
        const form = document.getElementById(`edit-form-${id}`);
        if (form) form.classList.toggle('hidden');
    } else if (action === 'del-mat') {
        deleteMaterial(id);
    } else if (action === 'del-claim') {
        deleteClaim(id);
    }
});

document.addEventListener('submit', (e) => {
    const form = e.target.closest('[data-edit-form]');
    if (form) saveMaterial(e, form.getAttribute('data-edit-form'));
});

// UI Helpers
function getKindColor(kind) {
    switch (kind) {
        case 'photo': return 'var(--badge-photo)';
        case 'chat_log': return 'var(--badge-chat)';
        case 'receipt': return 'var(--badge-receipt)';
        case 'document': return 'var(--badge-document)';
        default: return 'var(--text-muted)';
    }
}

function openModal(item) {
    document.getElementById('modal-title').textContent = item.filename;
    document.getElementById('modal-date').textContent = `Date: ${item.date || 'Unknown'}`;
    document.getElementById('modal-kind').textContent = `Kind: ${(item.kind || '').replace('_', ' ')}`;
    document.getElementById('modal-description').textContent = item.description || 'No description provided.';
    document.getElementById('modal-source').textContent = item.source_text || '[No text extracted]';

    const amountsDiv = document.getElementById('modal-amounts');
    if (item.amounts && item.amounts.length > 0) {
        amountsDiv.textContent = '';
        const strong = document.createElement('strong');
        strong.textContent = 'Detected Amounts: ';
        amountsDiv.appendChild(strong);
        amountsDiv.appendChild(document.createTextNode(item.amounts.map(a => '$' + a).join(', ')));
        amountsDiv.style.marginTop = '12px';
    } else {
        amountsDiv.textContent = '';
        amountsDiv.style.marginTop = '0';
    }

    els.modal.showModal();
}
