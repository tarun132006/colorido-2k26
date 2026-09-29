# app/main.py
import json, re, sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from .db import query, execute, init_db
from .seed import CATEGORIES
import csv, io, secrets
from fastapi import Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .seed import hash_pw, seed
from pathlib import Path
from fastapi.staticfiles import StaticFiles



app = FastAPI(title="COLORIDO 2K26")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

init_db()
seed()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.get("/api/ping")
def ping():
    return "pong"


def event_to_dict(row):
    d = dict(row)
    d["rules"] = json.loads(d["rules"]) if d.get("rules") else []
    return d


@app.get("/api/events")
def list_events(division: str | None = None, category: str | None = None,
                gender: str | None = None):
    sql, params = "SELECT * FROM events WHERE 1=1", []
    if division:
        sql += " AND lower(division) = lower(?)"
        params.append(division)
    if category:
        sql += " AND lower(category) = lower(?)"
        params.append(category)
    if gender:
        sql += " AND lower(gender) = lower(?)"
        params.append(gender)
    sql += " ORDER BY day, start_time"
    return [event_to_dict(r) for r in query(sql, tuple(params))]


@app.get("/api/events/{slug}")
def get_event(slug: str):
    rows = query("SELECT * FROM events WHERE slug = ?", (slug,))
    if not rows:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_to_dict(rows[0])


class RegisterIn(BaseModel):
    event_slug: str
    name: str
    email: str
    phone: str
    college: str
    gender: str
    team_name: str | None = None
    members: list[str] = Field(default_factory=list)

    @field_validator("name", "college")
    @classmethod
    def not_blank(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("This field is required")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        digits = re.sub(r"[\s\-]", "", v)
        digits = re.sub(r"^(\+91|0)", "", digits)
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits

    @field_validator("members")
    @classmethod
    def valid_members(cls, v):
        cleaned = [item.strip() for item in v if item and item.strip()]
        if len(cleaned) != len(v):
            return cleaned
        return cleaned

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, v):
        if v not in ("Male", "Female"):
            raise ValueError("Gender must be Male or Female")
        return v


@app.post("/api/register", status_code=201)
def register(data: RegisterIn):
    rows = query("SELECT * FROM events WHERE slug = ?", (data.event_slug,))
    if not rows:
        raise HTTPException(404, "Event not found")
    ev = rows[0]

    if ev["gender"] == "Boys" and data.gender != "Male":
        raise HTTPException(400, "This event is open to boys only")
    if ev["gender"] == "Girls" and data.gender != "Female":
        raise HTTPException(400, "This event is open to girls only")

    members = [m.strip() for m in data.members if m.strip()]
    size = 1 + len(members)
    if size < ev["team_min"] or size > ev["team_max"]:
        raise HTTPException(
            400, f"Team size must be between {ev['team_min']} and {ev['team_max']} "
                 f"(you entered {size})")
    if ev["team_max"] > 1 and not (data.team_name and data.team_name.strip()):
        raise HTTPException(400, "Team name is required for team events")

    if query("SELECT 1 FROM registrations WHERE event_id = ? AND email = ?",
             (ev["id"], data.email)):
        raise HTTPException(409, "This email is already registered for this event")

    try:
        execute(
            """INSERT INTO registrations
               (event_id, name, email, phone, college, gender, team_name, members)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ev["id"], data.name, data.email, data.phone, data.college,
             data.gender, (data.team_name or "").strip() or None,
             json.dumps(members)))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "This email is already registered for this event")

    row_id = query("SELECT id FROM registrations WHERE event_id = ? AND email = ?",
                   (ev["id"], data.email))[0]["id"]
    code = CATEGORIES[ev["category"]][1]
    reg_id = f"CLR26-{code}-{row_id:04d}"
    execute("UPDATE registrations SET reg_id = ? WHERE id = ?", (reg_id, row_id))

    return {"reg_id": reg_id, "event": ev["name"], "status": "Confirmed"}



# ---------- Admin ----------
bearer = HTTPBearer(auto_error=False)
SESSIONS = set()   # in-memory tokens; cleared when the server restarts


class LoginIn(BaseModel):
    username: str
    password: str


def require_admin(creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    token = creds.credentials if creds else None
    if not token or token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Admin login required", headers={"WWW-Authenticate": "Bearer"})


@app.post("/api/admin/login")
def admin_login(data: LoginIn):
    rows = query("SELECT * FROM admins WHERE username = ?", (data.username,))
    if not rows or not secrets.compare_digest(
            rows[0]["pw_hash"], hash_pw(data.password, rows[0]["salt"])):
        raise HTTPException(401, "Invalid username or password")
    token = secrets.token_hex(24)
    SESSIONS.add(token)
    return {"token": token}


def fetch_registrations(event_slug, college, gender, q):
    sql = """SELECT r.reg_id, e.name AS event, e.category, e.division,
                    r.name, r.email, r.phone, r.college, r.gender,
                    r.team_name, r.members, r.status, r.created_at
             FROM registrations r JOIN events e ON e.id = r.event_id
             WHERE 1=1"""
    params = []
    if event_slug:
        sql += " AND e.slug = ?"
        params.append(event_slug)
    if college:
        sql += " AND lower(r.college) LIKE lower(?)"
        params.append(f"%{college}%")
    if gender:
        sql += " AND r.gender = ?"
        params.append(gender)
    if q:
        sql += " AND (lower(r.name) LIKE lower(?) OR lower(r.email) LIKE lower(?) OR r.reg_id LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY r.id DESC"
    return [dict(r) for r in query(sql, tuple(params))]


@app.get("/api/admin/registrations", dependencies=[Depends(require_admin)])
def admin_registrations(event_slug: str | None = None, college: str | None = None,
                        gender: str | None = None, q: str | None = None):
    rows = fetch_registrations(event_slug, college, gender, q)
    for r in rows:
        r["members"] = json.loads(r["members"]) if r["members"] else []
    return {"count": len(rows), "registrations": rows}


@app.get("/api/admin/export.csv", dependencies=[Depends(require_admin)])
def admin_export(event_slug: str | None = None, college: str | None = None,
                 gender: str | None = None, q: str | None = None):
    rows = fetch_registrations(event_slug, college, gender, q)
    buf = io.StringIO()
    cols = ["reg_id", "event", "category", "division", "name", "email", "phone",
            "college", "gender", "team_name", "members", "status", "created_at"]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"})

# ---------- Public content ----------
@app.get("/api/announcements")
def announcements():
    return [dict(r) for r in query(
        "SELECT * FROM announcements ORDER BY pinned DESC, id DESC")]


@app.get("/api/results")
def results(event_slug: str | None = None):
    sql = """SELECT e.name AS event, e.slug, e.division, r.position, r.winner, r.college
             FROM results r JOIN events e ON e.id = r.event_id WHERE 1=1"""
    params = []
    if event_slug:
        sql += " AND e.slug = ?"
        params.append(event_slug)
    sql += " ORDER BY e.name, r.position"
    return [dict(r) for r in query(sql, tuple(params))]


@app.get("/api/gallery")
def gallery(category: str | None = None, year: int | None = None):
    sql, params = "SELECT * FROM gallery WHERE 1=1", []
    if category:
        sql += " AND lower(category) = lower(?)"
        params.append(category)
    if year:
        sql += " AND year = ?"
        params.append(year)
    return [dict(r) for r in query(sql + " ORDER BY id", tuple(params))]


@app.get("/api/sponsors")
def sponsors():
    return [dict(r) for r in query(
        """SELECT * FROM sponsors ORDER BY CASE tier
           WHEN 'Title' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END, id""")]


class ContactIn(BaseModel):
    name: str
    email: str
    subject: str | None = None
    body: str

    @field_validator("name", "body")
    @classmethod
    def not_blank(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("This field is required")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v


@app.post("/api/contact", status_code=201)
def contact(data: ContactIn):
    execute("INSERT INTO messages (name, email, subject, body) VALUES (?,?,?,?)",
            (data.name, data.email, data.subject, data.body))
    return {"status": "received"}


@app.get("/api/lookup")
def lookup(reg_id: str | None = None, email: str | None = None):
    if not reg_id and not email:
        raise HTTPException(400, "Provide a registration ID or email")
    sql = """SELECT r.reg_id, e.name AS event, e.day, e.start_time, e.venue,
                    r.name, r.college, r.team_name, r.status
             FROM registrations r JOIN events e ON e.id = r.event_id WHERE 1=1"""
    params = []
    if reg_id:
        sql += " AND r.reg_id = ?"
        params.append(reg_id.strip().upper())
    if email:
        sql += " AND r.email = ?"
        params.append(email.strip().lower())
    rows = query(sql, tuple(params))
    if not rows:
        raise HTTPException(404, "No registration found")
    return [dict(r) for r in rows]


# ---------- Admin: content ----------
class AnnouncementIn(BaseModel):
    title: str
    body: str
    pinned: bool = False


class ResultIn(BaseModel):
    event_slug: str
    position: int
    winner: str
    college: str | None = None


@app.post("/api/admin/announcements", status_code=201, dependencies=[Depends(require_admin)])
def post_announcement(data: AnnouncementIn):
    execute("INSERT INTO announcements (title, body, pinned) VALUES (?,?,?)",
            (data.title.strip(), data.body.strip(), int(data.pinned)))
    return {"status": "posted"}


@app.post("/api/admin/results", status_code=201, dependencies=[Depends(require_admin)])
def post_result(data: ResultIn):
    if data.position not in (1, 2, 3):
        raise HTTPException(400, "Position must be 1, 2 or 3")
    rows = query("SELECT id FROM events WHERE slug = ?", (data.event_slug,))
    if not rows:
        raise HTTPException(404, "Event not found")
    execute("INSERT INTO results (event_id, position, winner, college) VALUES (?,?,?,?)",
            (rows[0]["id"], data.position, data.winner.strip(), data.college))
    return {"status": "published"}


@app.get("/api/admin/messages", dependencies=[Depends(require_admin)])
def admin_messages():
    return [dict(r) for r in query("SELECT * FROM messages ORDER BY id DESC")]



STATIC = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")