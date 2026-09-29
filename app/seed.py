# app/seed.py
import hashlib, json, os, re
from .db import query, execute, init_db

# category: (division, code, gender, venue, rules)
CATEGORIES = {
    "Fine Arts": ("cultural", "FIN", "Open", "Arts Pavilion", [
        "Participants must bring their own materials unless stated otherwise.",
        "Work must be original and completed on the spot within the time limit.",
        "Judging criteria: creativity, technique and adherence to the theme.",
        "The decision of the judges is final."]),
    "Music & Band": ("cultural", "MUS", "Open", "Main Auditorium", [
        "Performance time limit applies; exceeding it leads to deductions.",
        "Karaoke tracks are allowed for solo singing; instruments must be carried by the team.",
        "Judging criteria: melody, rhythm, stage presence and overall impact.",
        "Vulgar or offensive lyrics lead to disqualification."]),
    "Dance": ("cultural", "DAN", "Open", "Open Air Theatre", [
        "Music must be submitted in .mp3 format to the coordinator before the event.",
        "Props are allowed but must be arranged by the team.",
        "Judging criteria: choreography, synchronisation, expression and costumes.",
        "The decision of the judges is final."]),
    "Choreoday": ("cultural", "CHO", "Open", "Open Air Theatre", [
        "Each team performs a choreography based on the theme announced on the day.",
        "Fusion of styles is allowed within the time limit.",
        "Judging criteria: theme interpretation, creativity, formation and energy."]),
    "Dramatics": ("cultural", "DRA", "Open", "Seminar Hall", [
        "Content must be free of political and religious references.",
        "Time limits are strict; the timer starts with the first dialogue or movement.",
        "Judging criteria: script, acting, direction and impact."]),
    "Fashion Show": ("cultural", "FAS", "Open", "Main Auditorium", [
        "Teams present a themed showcase with a maximum of one round.",
        "Costumes must be decent and suitable for a college audience.",
        "Judging criteria: theme, creativity, walk and coordination."]),
    "Tekraft Events": ("cultural", "TEK", "Open", "Innovation Lab", [
        "Participants must bring their own laptops or devices where required.",
        "Submissions must be original; plagiarism leads to disqualification.",
        "Judging criteria: creativity, technical quality and presentation."]),
    "Literary": ("cultural", "LIT", "Open", "Seminar Hall", [
        "The language of the event is English unless the event states otherwise.",
        "Topics are announced on the spot.",
        "Judging criteria: content, fluency, originality and time management."]),
    "Basketball": ("sports", "BAS", "Boys", "Main Ground", [
        "Matches follow standard FIBA rules with shortened quarters.",
        "Teams must report 15 minutes before their fixture or forfeit the match.",
        "Players must carry a valid college ID card.",
        "The referee's decision is final."]),
    "Volleyball": ("sports", "VOL", "Boys", "Main Ground", [
        "Matches are best of three sets to 25 points.",
        "Teams must report 15 minutes before their fixture or forfeit the match.",
        "Players must carry a valid college ID card."]),
    "Throwball": ("sports", "THR", "Girls", "Main Ground", [
        "Matches are best of three sets to 25 points.",
        "Teams must report 15 minutes before their fixture or forfeit the match.",
        "Players must carry a valid college ID card."]),
    "TenniKoit": ("sports", "TEN", "Girls", "Indoor Stadium", [
        "Singles and doubles follow standard tenniKoit rules.",
        "Matches are best of three sets.",
        "Players must carry a valid college ID card."]),
    "Table Tennis": ("sports", "TTB", "Boys", "Indoor Stadium", [
        "Matches are best of five games to 11 points.",
        "Players must carry a valid college ID card.",
        "The referee's decision is final."]),
}

# (category, name, team_min, team_max, description, gender override)
EVENTS = [
    ("Fine Arts", "Rangoli", 1, 2, "Create a themed rangoli using colours and natural materials.", None),
    ("Fine Arts", "Spot Painting", 1, 1, "Paint on the spot to a theme revealed at the start.", None),
    ("Fine Arts", "Clay Modelling", 1, 1, "Sculpt a figure from clay within the time limit.", None),
    ("Music & Band", "Solo Singing", 1, 1, "Perform a song of your choice in any language.", None),
    ("Music & Band", "Instrumental Solo", 1, 1, "Perform a solo on any instrument.", None),
    ("Music & Band", "Group Singing", 3, 8, "A choir or ensemble vocal performance.", None),
    ("Music & Band", "Battle of Bands", 4, 8, "Bands compete with live original or cover sets.", None),
    ("Dance", "Solo Dance", 1, 1, "A solo performance in any dance form.", None),
    ("Dance", "Group Dance", 4, 12, "A group performance in any dance form.", None),
    ("Choreoday", "Theme-Based Choreography", 8, 20, "Large-format choreography built around a theme.", None),
    ("Dramatics", "Skit", 5, 10, "A short stage play on a social or comic theme.", None),
    ("Dramatics", "Mime", 3, 6, "A story told through movement and expression without dialogue.", None),
    ("Dramatics", "Mono Act", 1, 1, "A solo acting performance.", None),
    ("Fashion Show", "Theme Fashion Walk", 8, 12, "A themed ramp showcase with original styling.", None),
    ("Tekraft Events", "Photography", 1, 1, "Submit photographs on the announced theme.", None),
    ("Tekraft Events", "Short Film", 2, 5, "Submit an original short film of up to five minutes.", None),
    ("Tekraft Events", "Poster Design", 1, 2, "Design a digital poster on the spot.", None),
    ("Literary", "Debate", 2, 2, "Two-member teams argue for and against a motion.", None),
    ("Literary", "Extempore", 1, 1, "Speak on a topic given moments before you begin.", None),
    ("Literary", "Quiz", 3, 3, "A general quiz with written and buzzer rounds.", None),
    ("Literary", "Creative Writing", 1, 1, "Write a short story or poem on a theme.", None),
    ("Basketball", "Basketball", 5, 10, "Knockout tournament for boys' teams.", None),
    ("Volleyball", "Volleyball", 6, 10, "Knockout tournament for boys' teams.", None),
    ("Table Tennis", "Table Tennis", 1, 1, "Singles knockout for boys.", "Boys"),
    ("Throwball", "Throwball", 7, 10, "Knockout tournament for girls' teams.", None),
    ("TenniKoit", "TenniKoit", 1, 2, "Singles and doubles for girls.", None),
    ("Table Tennis", "Table Tennis", 1, 1, "Singles knockout for girls.", "Girls"),
]

TIMES = ["09:30", "11:00", "14:00", "15:30"]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def seed():
    """Create the demo content without duplicating existing rows.

    This makes a fresh checkout immediately usable while remaining safe to
    run every time the application starts. Existing registrations are kept.
    """
    init_db()

    for i, (cat, name, tmin, tmax, desc, gender) in enumerate(EVENTS):
        division, code, default_gender, venue, rules = CATEGORIES[cat]
        gender = gender or default_gender
        slug = slugify(name + ("-" + gender if division == "sports" else ""))
        execute(
            """INSERT OR IGNORE INTO events (slug, name, division, category, gender, team_min, team_max,
               description, rules, eligibility, fee, prize, day, start_time, venue,
               coordinator, phone, featured)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (slug, name, division, cat, gender, tmin, tmax, desc, json.dumps(rules),
             "Open to all registered college students with a valid ID card.",
             0 if division == "cultural" and tmax == 1 else 100 * tmax // max(tmax, 1),
             "Cash prize and certificates", i % 3 + 1, TIMES[i % 4], venue,
             "Event Coordinator", "+91 90000 00000", 1 if i % 5 == 0 else 0),
        )

    for title, body, pinned in [
        ("Registrations are now open", "Register for cultural and sports events through the Register page.", 1),
        ("Schedule published", "The day-wise schedule is available on the Events page.", 0),
        ("Accommodation details", "Outstation participants can request accommodation through the Contact page.", 0),
    ]:
        if not query("SELECT id FROM announcements WHERE title = ?", (title,)):
            execute("INSERT INTO announcements (title, body, pinned) VALUES (?,?,?)", (title, body, pinned))

    for name, tier in [("Title Sponsor Co.", "Title"), ("Gold Partner One", "Gold"),
                       ("Gold Partner Two", "Gold"), ("Silver Partner One", "Silver"),
                       ("Silver Partner Two", "Silver"), ("Silver Partner Three", "Silver"),
                       ("Media Partner", "Partner"), ("Education Partner", "Partner")]:
        if not query("SELECT id FROM sponsors WHERE name = ?", (name,)):
            execute("INSERT INTO sponsors (name, tier) VALUES (?,?)", (name, tier))

    for caption, cat in [("Main stage, opening night", "Cultural"), ("Group dance finals", "Cultural"),
                         ("Battle of Bands", "Cultural"), ("Rangoli exhibition", "Cultural"),
                         ("Basketball semi-final", "Sports"), ("Volleyball court", "Sports"),
                         ("Throwball final", "Sports"), ("Prize distribution", "Sports")]:
        if not query("SELECT id FROM gallery WHERE caption = ?", (caption,)):
            execute("INSERT INTO gallery (caption, category, year) VALUES (?,?,?)", (caption, cat, 2025))

    salt = "colorido-salt"
    pw = os.environ.get("ADMIN_PASSWORD", "colorido@2026")
    if not query("SELECT username FROM admins WHERE username = ?", ("admin",)):
        execute("INSERT INTO admins (username, salt, pw_hash) VALUES (?,?,?)",
                ("admin", salt, hash_pw(pw, salt)))