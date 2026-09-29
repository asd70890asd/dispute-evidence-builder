import os
import re
import uuid
import json
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from PIL import Image
from PIL.ExifTags import TAGS
from pypdf import PdfReader

# Ensure sample assets exist
try:
    from sample_assets.generate_samples import generate_samples
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "sample_assets", "manifest.json")):
        generate_samples()
except ImportError:
    pass

app = FastAPI(title="CaseFile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
embedding_model = None
db_materials = {}
db_claims = {}


def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model


def cosine_similarity(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10))


class ClaimInput(BaseModel):
    text: str


class MaterialUpdate(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    kind: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


def extract_exif_date(image: Image.Image):
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == 'DateTimeOriginal':
                # EXIF format: YYYY:MM:DD HH:MM:SS
                dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                return dt.date().isoformat()
    except Exception:
        pass
    return None


def extract_amounts(text: str) -> List[float]:
    if not text:
        return []
    matches = re.findall(r'\$([\d,]+(?:\.\d{2})?)', text)
    amounts = []
    for m in matches:
        try:
            amounts.append(float(m.replace(',', '')))
        except ValueError:
            continue
    return amounts


@app.post("/api/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    date: Optional[str] = Form(None),
    description: Optional[str] = Form(""),
    kind: Optional[str] = Form(None)
):
    disallowed = {'.exe', '.bat', '.sh', '.dll'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in disallowed:
        raise HTTPException(status_code=400, detail="File extension not allowed")

    content_bytes = await file.read()
    source_text = ""
    extracted_date = date
    derived_kind = kind

    if not derived_kind:
        if ext in {'.jpg', '.jpeg', '.png'}:
            derived_kind = 'photo'
        elif ext == '.txt':
            derived_kind = 'chat_log'
        elif ext == '.pdf':
            derived_kind = 'document'
        else:
            derived_kind = 'document'

    # Processing based on file type
    if ext in {'.jpg', '.jpeg', '.png'}:
        import io
        try:
            img = Image.open(io.BytesIO(content_bytes))
            if not extracted_date:
                extracted_date = extract_exif_date(img)
        except Exception:
            pass
    elif ext == '.txt':
        try:
            source_text = content_bytes.decode('utf-8')[:2000]
        except Exception:
            pass
    elif ext == '.pdf':
        import io
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
            texts = [page.extract_text() for page in reader.pages if page.extract_text()]
            source_text = "\n".join(texts)[:2000]
        except Exception:
            pass

    amounts = extract_amounts(source_text)

    mat_id = str(uuid.uuid4())
    material = {
        "id": mat_id,
        "filename": file.filename,
        "kind": derived_kind,
        "date": extracted_date,
        "description": description,
        "source_text": source_text,
        "amounts": amounts
    }
    db_materials[mat_id] = material
    return material


@app.get("/api/materials")
def get_materials():
    return list(db_materials.values())


@app.patch("/api/materials/{mat_id}")
def update_material(mat_id: str, update: MaterialUpdate):
    if mat_id not in db_materials:
        raise HTTPException(status_code=404, detail="Material not found")

    mat = db_materials[mat_id]
    if update.date is not None:
        mat['date'] = update.date
    if update.description is not None:
        mat['description'] = update.description
    if update.kind is not None:
        mat['kind'] = update.kind

    return mat


@app.delete("/api/materials/{mat_id}")
def delete_material(mat_id: str):
    if mat_id in db_materials:
        del db_materials[mat_id]
    # Remove from claims matches as well
    for claim in db_claims.values():
        claim['matches'] = [m for m in claim['matches'] if m['material_id'] != mat_id]
    return {"status": "deleted"}


@app.post("/api/case/reset")
def reset_case():
    db_materials.clear()
    db_claims.clear()
    return {"status": "reset"}


@app.post("/api/case/sample")
def load_sample_case():
    reset_case()
    base_dir = os.path.join(os.path.dirname(__file__), "sample_assets")
    manifest_path = os.path.join(base_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        from sample_assets.generate_samples import generate_samples
        generate_samples()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for item in manifest:
        file_path = os.path.join(base_dir, item["filename"])
        source_text = ""
        ext = os.path.splitext(item["filename"])[1].lower()
        if ext == '.txt' and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                source_text = f.read()[:2000]

        mat_id = str(uuid.uuid4())
        amounts = extract_amounts(source_text)
        db_materials[mat_id] = {
            "id": mat_id,
            "filename": item["filename"],
            "kind": item["kind"],
            "date": item["date"],
            "description": item["description"],
            "source_text": source_text,
            "amounts": amounts
        }

    preset_claims = [
        "The living room wall had no damage at move-in.",
        "I reported the kitchen leak to the landlord in March 2026.",
        "The landlord withheld $800 from my deposit.",
        "I paid $180 for professional cleaning before moving out.",
        "The move-out inspection happened on August 30 with the superintendent present."
    ]

    for c_text in preset_claims:
        process_claim(c_text)

    return {"materials": len(db_materials), "claims": len(db_claims)}


@app.get("/api/timeline")
def get_timeline():
    mats = list(db_materials.values())
    dated = [m for m in mats if m['date']]
    undated = [m for m in mats if not m['date']]

    dated.sort(key=lambda x: x['date'])
    return dated + undated


def process_claim(text: str):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Claim text cannot be empty")

    model = get_embedding_model()
    claim_embed = model.encode(text)

    matches = []
    for mat in db_materials.values():
        content_to_embed = f"{mat.get('description', '')} {mat.get('source_text', '')[:500]}".strip()
        if not content_to_embed:
            continue

        mat_embed = model.encode(content_to_embed)
        score = cosine_similarity(claim_embed, mat_embed)

        if score >= 0.25:
            matches.append({"material_id": mat['id'], "score": round(score, 3)})

    matches.sort(key=lambda x: x['score'], reverse=True)
    top_matches = matches[:3]

    status = "no_evidence"
    if top_matches:
        max_score = top_matches[0]['score']
        if max_score >= 0.55:
            status = "supported"
        elif max_score >= 0.35:
            status = "partial"

    claim_id = str(uuid.uuid4())
    db_claims[claim_id] = {
        "id": claim_id,
        "text": text,
        "status": status,
        "matches": top_matches
    }
    return db_claims[claim_id]


@app.post("/api/claims")
def add_claim(claim: ClaimInput):
    return process_claim(claim.text)


@app.get("/api/claims")
def get_claims():
    expanded = []
    for claim in db_claims.values():
        c_copy = dict(claim)
        c_matches = []
        for m in claim['matches']:
            mat = db_materials.get(m['material_id'])
            if mat:
                c_matches.append({
                    "score": m['score'],
                    "material_id": mat['id'],
                    "filename": mat['filename'],
                    "date": mat['date'],
                    "description_summary": mat.get('description', '')[:80]
                })
        c_copy['matches'] = c_matches
        expanded.append(c_copy)
    return expanded


@app.delete("/api/claims/{claim_id}")
def delete_claim(claim_id: str):
    if claim_id in db_claims:
        del db_claims[claim_id]
    return {"status": "deleted"}


@app.get("/api/gaps")
def get_gaps():
    unsupported = [c for c in db_claims.values() if c['status'] == 'no_evidence']
    undated = [{"id": m['id'], "filename": m['filename']} for m in db_materials.values() if not m['date']]
    return {
        "unsupported_claims": unsupported,
        "undated_materials": undated
    }


@app.get("/api/inconsistencies")
def get_inconsistencies():
    if not db_materials:
        return []

    model = get_embedding_model()
    mats = list(db_materials.values())
    n = len(mats)

    embeddings = []
    for m in mats:
        text = f"{m.get('description', '')} {m.get('source_text', '')[:500]}".strip()
        embeddings.append(model.encode(text) if text else np.zeros(384))

    adj_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if np.any(embeddings[i]) and np.any(embeddings[j]):
                score = cosine_similarity(embeddings[i], embeddings[j])
                if score >= 0.60:
                    adj_matrix[i, j] = 1
                    adj_matrix[j, i] = 1

    visited = set()
    clusters = []

    for i in range(n):
        if i not in visited:
            cluster = []
            queue = [i]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    cluster.append(curr)
                    for j in range(n):
                        if adj_matrix[curr, j] == 1 and j not in visited:
                            queue.append(j)
            if len(cluster) >= 2:
                clusters.append(cluster)

    reports = []
    for cluster_indices in clusters:
        cluster_amounts = []
        cluster_mat_ids = []
        for idx in cluster_indices:
            mat = mats[idx]
            cluster_mat_ids.append(mat['id'])
            if mat['amounts']:
                cluster_amounts.extend(mat['amounts'])

        distinct_amounts = list(set(cluster_amounts))
        if len(distinct_amounts) >= 2:
            max_amt = max(distinct_amounts)
            min_amt = min(distinct_amounts)
            if (max_amt - min_amt) > 50:
                reports.append({
                    "material_ids": cluster_mat_ids,
                    "amounts": distinct_amounts,
                    "note": f"Materials describe a similar matter but state different amounts (${max_amt:g} vs ${min_amt:g}). Please review."
                })

    return reports


@app.get("/api/report", response_class=HTMLResponse)
def get_report():
    timeline = get_timeline()
    claims = get_claims()
    gaps = get_gaps()
    inconsistencies = get_inconsistencies()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>CaseFile Evidence Brief</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; color: #333; line-height: 1.5; }
            h1, h2 { color: #2c3e50; }
            .disclaimer { background: #fff3cd; color: #856404; padding: 15px; border: 1px solid #ffeeba; margin-bottom: 30px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #f8f9fa; }
            .status-supported { color: green; font-weight: bold; }
            .status-partial { color: orange; font-weight: bold; }
            .status-no_evidence { color: red; font-weight: bold; }
            .alert { background: #f8d7da; color: #721c24; padding: 10px; border: 1px solid #f5c6cb; margin-bottom: 10px; }
            @media print { .disclaimer { border-color: #000; } }
        </style>
    </head>
    <body>
        <h1>Evidence Brief</h1>
        <div class="disclaimer">
            CaseFile organizes your materials. It is not legal advice and not a substitute for a lawyer. All data in this sample is synthetic and fictional.
        </div>

        <h2>1. Timeline of Events</h2>
        <table>
            <tr><th>Date</th><th>Description</th><th>Source File</th></tr>
    """

    for item in timeline:
        date_str = item['date'] if item['date'] else "Undated"
        html += f"<tr><td>{date_str}</td><td>{item.get('description', '')}</td><td>{item['filename']}</td></tr>"

    html += """
        </table>

        <h2>2. Claims Analysis</h2>
        <table>
            <tr><th>Claim</th><th>Status</th><th>Cited Materials</th></tr>
    """

    for claim in claims:
        citations = "<br>".join([f"- {m['filename']} (Score: {m['score']})" for m in claim['matches']])
        if not citations:
            citations = "None"

        html += f"<tr><td>{claim['text']}</td><td class='status-{claim['status']}'>{claim['status'].replace('_', ' ').title()}</td><td>{citations}</td></tr>"

    html += """
        </table>

        <h2>3. Evidence Gaps & Inconsistencies</h2>
    """

    if inconsistencies:
        for inc in inconsistencies:
            html += f"<div class='alert'><strong>Inconsistency Detected:</strong> {inc['note']}</div>"

    if gaps['unsupported_claims']:
        html += "<h3>Unsupported Claims</h3><ul>"
        for c in gaps['unsupported_claims']:
            html += f"<li>{c['text']}</li>"
        html += "</ul>"

    if gaps['undated_materials']:
        html += "<h3>Undated Materials</h3><ul>"
        for m in gaps['undated_materials']:
            html += f"<li>{m['filename']}</li>"
        html += "</ul>"

    if not inconsistencies and not gaps['unsupported_claims'] and not gaps['undated_materials']:
        html += "<p>No significant gaps or inconsistencies detected.</p>"

    html += """
    </body>
    </html>
    """

    return html
