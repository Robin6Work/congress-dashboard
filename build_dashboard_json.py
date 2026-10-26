#!/usr/bin/env python3
"""
Builds data/congress_dashboard.json for the Power BI member-card dashboard.

Downloads three public JSON files from the unitedstates/congress-legislators project,
flattens them into tables, pre-builds each member's HTML card, and writes ONE json file.

Usage:
    python scripts/build_dashboard_json.py
    python scripts/build_dashboard_json.py --legislators a.json --committees b.json --membership c.json   (offline test)

Environment variables (all optional):
    PHOTO_URL_TEMPLATE   default https://theunitedstates.io/images/congress/225x275/{id}.jpg
    SECTIONS_OPEN        "true" (default) renders card sections expanded, "false" collapsed
"""
import argparse
import html
import json
import os
import sys
import urllib.request
from datetime import date

BASE = "https://unitedstates.github.io/congress-legislators/"
URLS = {
    "legislators": BASE + "legislators-current.json",
    "committees": BASE + "committees-current.json",
    "membership": BASE + "committee-membership-current.json",
}
PHOTO_TEMPLATE = os.environ.get(
    "PHOTO_URL_TEMPLATE", "https://theunitedstates.io/images/congress/225x275/{id}.jpg"
)
SECTIONS_OPEN = os.environ.get("SECTIONS_OPEN", "true").strip().lower() == "true"

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia", "AS": "American Samoa", "GU": "Guam",
    "MP": "Northern Mariana Islands", "PR": "Puerto Rico", "VI": "Virgin Islands",
}

# State outlines: code -> (viewBox, SVG path). Add more states here; states without an
# entry get a plain box showing the two-letter code.
STATE_SHAPES = {
    "WA": ("0 0 76 51", "M20.4,2.0 L74.0,2.0 L73.9,37.6 L69.8,43.4 L55.8,43.4 L52.8,44.3 L46.2,45.8 L37.8,48.2 L35.0,48.2 L28.5,47.5 L24.0,49.3 L20.3,48.2 L19.1,43.4 L16.3,41.3 L10.7,39.9 L8.4,39.6 L7.9,30.9 L7.0,24.1 L5.1,19.2 L2.9,17.2 L2.0,10.5 L7.9,11.6 L13.5,13.7 L17.2,14.1 L20.5,14.1 L21.4,18.5 L20.0,24.1 L19.1,28.9 L22.9,26.8 L24.0,21.3 L25.7,15.8 L23.3,11.6 L22.9,5.4 Z"),
    "VT": ("0 0 38 60", "M3.1,2.0 L35.6,2.0 L34.8,7.2 L34.6,12.8 L32.5,15.5 L25.9,19.4 L25.7,23.1 L25.0,27.1 L21.5,33.7 L21.1,35.4 L19.9,39.6 L18.8,44.0 L18.8,48.2 L17.1,55.1 L18.6,58.0 L4.3,57.6 L4.1,37.9 L2.0,36.1 L2.4,29.3 L2.9,19.4 L2.4,12.1 Z"),
    "FL": ("0 0 70 62", "M2.0,2.0 L24.7,2.0 L25.9,4.9 L40.8,5.8 L49.1,6.2 L55.6,4.9 L56.1,9.9 L57.2,12.9 L59.5,19.8 L63.5,27.2 L65.2,35.1 L68.0,44.5 L67.0,53.4 L65.6,58.3 L58.7,59.8 L54.3,52.9 L52.6,49.9 L50.8,46.5 L49.1,42.5 L46.5,38.1 L44.7,33.6 L43.8,31.6 L44.7,22.8 L41.7,20.8 L36.9,12.9 L32.5,11.4 L21.6,15.0 L18.6,10.4 L11.6,7.9 L4.6,8.4 L2.0,9.1 Z")
}

# Column schema (name -> type). Also used to generate the Power BI queries.
SCHEMA = {
    "legislators": [
        ("Bioguide ID", "text"), ("GovTrack ID", "int"), ("OpenSecrets ID", "text"),
        ("First Name", "text"), ("Middle Name", "text"), ("Last Name", "text"),
        ("Suffix", "text"), ("Nickname", "text"), ("Full Name", "text"),
        ("Birthday", "date"), ("Gender", "text"), ("Current Chamber", "text"),
        ("Current State", "text"), ("Current District", "int"), ("Senate Class", "int"),
        ("State Rank", "text"), ("Current Party", "text"), ("Caucus", "text"),
        ("Current Term Start", "date"), ("Current Term End", "date"), ("First Term Start", "date"),
        ("Total Terms", "int"), ("Website", "text"), ("Office", "text"), ("Address", "text"),
        ("Phone", "text"),
    ],
    "terms": [
        ("Bioguide ID", "text"), ("Term Number", "int"), ("Is Current Term", "bool"),
        ("Chamber", "text"), ("Start", "date"), ("End", "date"), ("State", "text"),
        ("District", "int"), ("Senate Class", "int"), ("State Rank", "text"),
        ("Party", "text"), ("Caucus", "text"), ("How Appointed", "text"),
    ],
    "leadership": [
        ("Bioguide ID", "text"), ("Title", "text"), ("Chamber", "text"),
        ("Start", "date"), ("End", "date"),
    ],
    "committees": [
        ("Committee ID", "text"), ("Parent Committee ID", "text"), ("Committee Group", "text"),
        ("Committee Name", "text"), ("Display Name", "text"), ("Chamber", "text"),
        ("Level", "text"), ("Sort Key", "text"), ("Website", "text"),
    ],
    "member_committees": [
        ("Committee ID", "text"), ("Bioguide ID", "text"), ("Role", "text"),
        ("Role Sort", "int"), ("Party Side", "text"), ("Rank", "int"),
    ],
    "cards": [("Bioguide ID", "text"), ("Card Sort", "int"), ("Card HTML", "text")],
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "congress-dashboard-builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def load(path_or_none, key):
    if path_or_none:
        with open(path_or_none, encoding="utf-8") as f:
            return json.load(f)
    return fetch(URLS[key])


def esc(t):
    return html.escape(t if t is not None else "", quote=True)


def fmt_date(s):
    if not s:
        return "\u2014"
    y, m, d = (int(x) for x in s.split("-"))
    return f"{date(y, m, d):%b} {d}, {y}"


def chamber_name(t):
    return {"house": "House", "senate": "Senate", "joint": "Joint"}.get(t, (t or "").title())


# ---------------------------------------------------------------- tables
def build_legislators(raw):
    leg, terms, lead = [], [], []
    for r in raw:
        ids, nm, bio, tl = r["id"], r.get("name", {}), r.get("bio", {}), r["terms"]
        first, last = tl[0], tl[-1]
        bg = ids["bioguide"]
        leg.append({
            "Bioguide ID": bg,
            "GovTrack ID": ids.get("govtrack"),
            "OpenSecrets ID": ids.get("opensecrets"),
            "First Name": nm.get("first"), "Middle Name": nm.get("middle"),
            "Last Name": nm.get("last"), "Suffix": nm.get("suffix"),
            "Nickname": nm.get("nickname"), "Full Name": nm.get("official_full"),
            "Birthday": bio.get("birthday"), "Gender": bio.get("gender"),
            "Current Chamber": "Senate" if last["type"] == "sen" else "House",
            "Current State": last["state"],
            "Current District": last.get("district"),
            "Senate Class": last.get("class"),
            "State Rank": last.get("state_rank"),
            "Current Party": last["party"],
            "Caucus": last.get("caucus"),
            "Current Term Start": last["start"], "Current Term End": last["end"],
            "First Term Start": first["start"],
            "Total Terms": len(tl),
            "Website": last.get("url"),
            "Office": last.get("office"),
            "Address": last.get("address"),
            "Phone": last.get("phone"),
        })
        for i, t in enumerate(tl):
            terms.append({
                "Bioguide ID": bg, "Term Number": i + 1, "Is Current Term": i == len(tl) - 1,
                "Chamber": "Senate" if t["type"] == "sen" else "House",
                "Start": t["start"], "End": t["end"], "State": t["state"],
                "District": t.get("district"), "Senate Class": t.get("class"),
                "State Rank": t.get("state_rank"), "Party": t["party"],
                "Caucus": t.get("caucus"), "How Appointed": t.get("how"),
            })
        for l in r.get("leadership_roles") or []:
            lead.append({
                "Bioguide ID": bg, "Title": l["title"],
                "Chamber": (l.get("chamber") or "").title(),
                "Start": l.get("start"), "End": l.get("end"),
            })
    return leg, terms, lead


def build_committees(raw):
    rows = []
    for c in raw:
        pid, pname = str(c["thomas_id"]), c["name"]
        ch = chamber_name(c.get("type"))
        rows.append({
            "Committee ID": pid, "Parent Committee ID": None, "Committee Group": pname,
            "Committee Name": pname, "Display Name": "Full committee", "Chamber": ch,
            "Level": "Committee", "Sort Key": pname + "|0", "Website": c.get("url"),
        })
        for s in c.get("subcommittees") or []:
            rows.append({
                "Committee ID": pid + str(s["thomas_id"]), "Parent Committee ID": pid,
                "Committee Group": pname, "Committee Name": s["name"], "Display Name": s["name"],
                "Chamber": ch, "Level": "Subcommittee",
                "Sort Key": pname + "|1|" + s["name"], "Website": None,
            })
    return rows


def role_sort(title):
    t = (title or "").lower()
    if "vice" in t:
        return 2
    if "chair" in t:
        return 1
    if "ranking" in t:
        return 3
    return 4


def build_member_committees(raw):
    rows = []
    for cid, members in raw.items():
        for m in members:
            title = m.get("title") or "Member"
            side = m.get("party")
            rows.append({
                "Committee ID": cid, "Bioguide ID": m["bioguide"], "Role": title,
                "Role Sort": role_sort(title),
                "Party Side": side.title() if side else None, "Rank": m.get("rank"),
            })
    return rows


# ---------------------------------------------------------------- cards
def colors(key):
    if key == "Democrat":
        return "#1D4E89", "#DCE6F2"
    if key == "Republican":
        return "#B42318", "#F6DAD7"
    return "#4B5563", "#E5E7EB"


CHEV = ('<svg class="chev" width="16" height="16" viewBox="0 0 16 16" fill="none" '
        'stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6l5 5 5-5"/></svg>')


def row_html(k, v):
    return f'<div class="row"><span class="k">{k}</span><span class="v">{v}</span></div>'


def sec_html(title, inner):
    open_attr = " open" if SECTIONS_OPEN else ""
    return (f'<details class="sec"{open_attr}><summary>{title}{CHEV}</summary>'
            f'<div class="body">{inner}</div></details>')


def committee_html_by_member(committees, member_committees):
    by_id = {c["Committee ID"]: c for c in committees}
    per = {}
    orphans = set()
    for mc in member_committees:
        c = by_id.get(mc["Committee ID"])
        if c is None:
            orphans.add(mc["Committee ID"])
            continue
        cls = "cm" if c["Level"] == "Committee" else "sub"
        line = (f'<div class="{cls}"><span>{esc(c["Committee Name"])}</span>'
                f'<span class="r">{esc(mc["Role"])}</span></div>')
        per.setdefault(mc["Bioguide ID"], []).append((c["Sort Key"], line))
    return {bg: "".join(l for _, l in sorted(v, key=lambda x: x[0])) for bg, v in per.items()}, orphans


def build_card(r, leadership_text, committees_html):
    key = r["Caucus"] if r["Caucus"] else r["Current Party"]
    dark, tint = colors(key)
    is_sen = r["Current Chamber"] == "Senate"
    st = r["Current State"]
    st_name = STATE_NAMES.get(st, st)
    d = r["Current District"]
    dist = None if d is None else ("At-Large" if d == 0 else f"District {d}")
    place = st_name if (is_sen or dist is None) else f"{st_name} \u00b7 {dist}"
    if is_sen:
        title = "U.S. Senator" + (f" \u00b7 {r['State Rank'].title()}" if r["State Rank"] else "")
    elif st == "PR":
        title = "Resident Commissioner"
    elif st in ("AS", "DC", "GU", "MP", "VI"):
        title = "U.S. Delegate"
    else:
        title = "U.S. Representative"
    first, last = r["First Name"] or "", r["Last Name"] or ""
    if r["Nickname"]:
        disp = f"{first} \u201c{r['Nickname']}\u201d {last}"
    else:
        disp = r["Full Name"] or f"{first} {last}"
    initials = first[:1] + last[:1]
    chamber_label = "Senate" if is_sen else "House of Representatives"
    if r["Caucus"] and r["Caucus"] != r["Current Party"]:
        party_label = f"{esc(r['Current Party'])}<br>Caucuses with {esc(r['Caucus'])}s"
    else:
        party_label = esc(r["Current Party"])
    photo = PHOTO_TEMPLATE.replace("{id}", r["Bioguide ID"])
    if st in STATE_SHAPES:
        vb, path = STATE_SHAPES[st]
        shape = (f'<svg class="state" viewBox="{vb}" role="img" aria-label="Outline of {esc(st_name)}">'
                 f'<path d="{path}" fill="{tint}" stroke="{dark}" stroke-width="2" stroke-linejoin="round"/></svg>')
    else:
        shape = f'<div class="stateBox" style="border-color:{dark};color:{dark}">{esc(st)}</div>'

    addr = r["Address"]
    zip_ = addr.rsplit("DC ", 1)[1].strip() if addr and "DC " in addr else None
    if r["Office"]:
        office_line = esc(r["Office"]) + ", Washington, DC" + (" " + esc(zip_) if zip_ else "")
    else:
        office_line = "\u2014"
    phone_html = (f'<a href="tel:{esc(r["Phone"])}">{esc(r["Phone"])}</a>' if r["Phone"] else "\u2014")
    site = r["Website"]
    if site:
        host = site.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        site_html = f'<a href="{esc(site)}">{esc(host)}</a>'
    else:
        site_html = "\u2014"

    service = (row_html("In Congress since", fmt_date(r["First Term Start"]))
               + row_html("Terms served", str(r["Total Terms"]))
               + row_html("Current term ends", fmt_date(r["Current Term End"]))
               + row_html("Leadership", esc(leadership_text) if leadership_text else "\u2014"))
    contact = (row_html("Office", office_line) + row_html("Phone", phone_html)
               + row_html("Website", site_html))
    committees = committees_html or '<div class="row"><span class="v">No committee assignments listed</span></div>'

    return (
        '<article class="card">'
        f'<div class="banner" style="background:{dark}"><span>{chamber_label}</span>'
        f'<span class="party">{party_label}</span></div>'
        '<div class="head">'
        f'<div class="photo"><span>{esc(initials)}</span><img src="{esc(photo)}" alt=""/></div>'
        f'<div class="hd"><h2 class="name">{esc(disp)}</h2><div class="place">{esc(place)}</div>'
        f'<div class="role">{title}</div></div>'
        f'{shape}</div>'
        + sec_html("Service record", service)
        + sec_html("Office &amp; contact", contact)
        + sec_html("Committees", committees)
        + "</article>"
    )


def build_cards(leg, lead, committees, member_committees):
    lead_by = {}
    for l in lead:
        if l["End"] is None:
            lead_by.setdefault(l["Bioguide ID"], []).append(l["Title"])
    cm_html, orphans = committee_html_by_member(committees, member_committees)

    def sort_key(r):
        return (0 if r["Current Chamber"] == "Senate" else 1,
                STATE_NAMES.get(r["Current State"], r["Current State"]),
                r["Last Name"] or "", r["First Name"] or "")

    cards = []
    for i, r in enumerate(sorted(leg, key=sort_key), start=1):
        bg = r["Bioguide ID"]
        cards.append({
            "Bioguide ID": bg, "Card Sort": i,
            "Card HTML": build_card(r, "; ".join(lead_by.get(bg, [])), cm_html.get(bg)),
        })
    return cards, orphans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legislators")
    ap.add_argument("--committees")
    ap.add_argument("--membership")
    ap.add_argument("--out", default="data/congress_dashboard.json")
    a = ap.parse_args()

    raw_leg = load(a.legislators, "legislators")
    raw_com = load(a.committees, "committees")
    raw_mem = load(a.membership, "membership")

    leg, terms, lead = build_legislators(raw_leg)
    committees = build_committees(raw_com)
    member_committees = build_member_committees(raw_mem)
    cards, orphans = build_cards(leg, lead, committees, member_committees)

    if not a.legislators and len(leg) < 400:
        sys.exit(f"Only {len(leg)} legislators found; expected ~535. Refusing to publish.")
    if orphans:
        print(f"WARNING: {len(orphans)} membership committee IDs have no match in committees "
              f"(e.g. {sorted(orphans)[:5]}). Subcommittee ID assumption may be wrong.")

    out = {
        "generated_on": date.today().isoformat(),
        "legislators": leg, "terms": terms, "leadership": lead,
        "committees": committees, "member_committees": member_committees, "cards": cards,
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print({k: len(v) for k, v in out.items() if isinstance(v, list)},
          f"-> {a.out} ({os.path.getsize(a.out)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
