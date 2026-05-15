"""
Bilateral diaspora weights for Eurovision voting countries.

DIASPORA_K[(voter_cc, performer_cc)] = approximate number of performer_cc
nationals living in voter_cc (in thousands, 2022-2024 estimates).

Sources: Eurostat migration statistics, Wikipedia, national statistics offices.

Usage: diaspora_score(voter_cc, performer_cc) → float [0, 1]
       Normalised log10 diaspora size. 0 = no known diaspora, 1 = largest.
"""
import math

# (voter_cc, performer_cc): diaspora in thousands
# = How many people from performer_cc live in voter_cc?
DIASPORA_K: dict[tuple[str, str], float] = {

    # ── Romanians abroad ─────────────────────────────────────────────────
    ("IT", "RO"): 1050, ("DE", "RO"): 800, ("ES", "RO"): 650,
    ("GB", "RO"): 400,  ("FR", "RO"): 200, ("AT", "RO"): 110,
    ("BE", "RO"): 80,   ("CH", "RO"): 75,  ("IE", "RO"): 45,
    ("GR", "RO"): 50,   ("PT", "RO"): 25,  ("CY", "RO"): 20,
    ("DK", "RO"): 20,   ("SE", "RO"): 15,  ("NO", "RO"): 15,
    ("CZ", "RO"): 12,   ("PL", "RO"): 10,  ("LU", "RO"): 10,

    # ── Albanians abroad ─────────────────────────────────────────────────
    ("IT", "AL"): 500,  ("GR", "AL"): 400, ("CH", "AL"): 180,
    ("DE", "AL"): 150,  ("GB", "AL"): 60,  ("AT", "AL"): 35,
    ("BE", "AL"): 25,   ("SE", "AL"): 25,  ("NO", "AL"): 18,
    ("FR", "AL"): 20,   ("DK", "AL"): 10,

    # ── Serbians abroad ──────────────────────────────────────────────────
    ("DE", "RS"): 700,  ("AT", "RS"): 300, ("CH", "RS"): 200,
    ("SE", "RS"): 80,   ("FR", "RS"): 60,  ("BE", "RS"): 50,
    ("AU", "RS"): 40,   ("IT", "RS"): 35,  ("GB", "RS"): 30,
    ("NO", "RS"): 20,   ("DK", "RS"): 15,  ("LU", "RS"): 10,

    # ── Croatians abroad ─────────────────────────────────────────────────
    ("DE", "HR"): 400,  ("AT", "HR"): 200, ("CH", "HR"): 100,
    ("AU", "HR"): 55,   ("SE", "HR"): 40,  ("GB", "HR"): 30,
    ("FR", "HR"): 20,   ("BE", "HR"): 15,  ("DK", "HR"): 10,

    # ── Montenegrins abroad ──────────────────────────────────────────────
    ("DE", "ME"): 80,   ("AT", "ME"): 45,  ("CH", "ME"): 30,
    ("SE", "ME"): 20,   ("IT", "ME"): 15,  ("FR", "ME"): 10,
    ("GB", "ME"): 10,   ("NO", "ME"): 8,

    # ── Poles abroad ─────────────────────────────────────────────────────
    ("DE", "PL"): 700,  ("GB", "PL"): 600, ("NO", "PL"): 100,
    ("IE", "PL"): 100,  ("SE", "PL"): 60,  ("AT", "PL"): 60,
    ("BE", "PL"): 55,   ("FR", "PL"): 55,  ("IT", "PL"): 50,
    ("DK", "PL"): 45,   ("CH", "PL"): 40,  ("NL", "PL"): 170,
    ("GR", "PL"): 10,   ("PT", "PL"): 12,  ("LU", "PL"): 8,
    ("FI", "PL"): 8,    ("CZ", "PL"): 20,  ("LV", "PL"): 5,

    # ── Ukrainians abroad (post-2022 massively increased) ───────────────
    ("DE", "UA"): 1500, ("PL", "UA"): 1000,("IT", "UA"): 350,
    ("CZ", "UA"): 300,  ("ES", "UA"): 200, ("AT", "UA"): 80,
    ("SE", "UA"): 65,   ("FR", "UA"): 55,  ("BE", "UA"): 45,
    ("CH", "UA"): 45,   ("GB", "UA"): 120, ("FI", "UA"): 22,
    ("NO", "UA"): 28,   ("PT", "UA"): 35,  ("IE", "UA"): 35,
    ("NL", "UA"): 120,  ("DK", "UA"): 30,  ("GR", "UA"): 20,
    ("LV", "UA"): 15,   ("LT", "UA"): 15,  ("EE", "UA"): 10,

    # ── Bulgarians abroad ────────────────────────────────────────────────
    ("DE", "BG"): 500,  ("ES", "BG"): 200, ("GB", "BG"): 150,
    ("GR", "BG"): 100,  ("IT", "BG"): 80,  ("FR", "BG"): 60,
    ("AT", "BG"): 50,   ("BE", "BG"): 35,  ("CY", "BG"): 20,
    ("CH", "BG"): 25,   ("PT", "BG"): 20,  ("SE", "BG"): 15,
    ("RO", "BG"): 10,   ("DK", "BG"): 10,  ("NL", "BG"): 30,

    # ── Armenians abroad ─────────────────────────────────────────────────
    ("FR", "AM"): 500,  ("DE", "AM"): 80,  ("BE", "AM"): 50,
    ("GB", "AM"): 60,   ("AU", "AM"): 35,  ("GR", "AM"): 45,
    ("CY", "AM"): 25,   ("IL", "AM"): 35,  ("SE", "AM"): 10,
    ("CH", "AM"): 10,   ("AT", "AM"): 8,

    # ── Moldovans abroad ─────────────────────────────────────────────────
    ("IT", "MD"): 200,  ("RO", "MD"): 200, ("DE", "MD"): 70,
    ("FR", "MD"): 70,   ("GB", "MD"): 60,  ("PT", "MD"): 35,
    ("ES", "MD"): 30,   ("BE", "MD"): 22,  ("IE", "MD"): 22,
    ("GR", "MD"): 15,   ("CY", "MD"): 10,  ("AT", "MD"): 10,

    # ── Georgians abroad ─────────────────────────────────────────────────
    ("GR", "GE"): 50,   ("DE", "GE"): 55,  ("IT", "GE"): 35,
    ("IL", "GE"): 80,   ("FR", "GE"): 25,  ("AU", "GE"): 10,
    ("AT", "GE"): 10,   ("SE", "GE"): 8,   ("GB", "GE"): 15,
    ("CY", "GE"): 8,    ("UA", "GE"): 30,

    # ── Lithuanians abroad ───────────────────────────────────────────────
    ("GB", "LT"): 200,  ("DE", "LT"): 80,  ("NO", "LT"): 80,
    ("IE", "LT"): 70,   ("SE", "LT"): 35,  ("DK", "LT"): 22,
    ("BE", "LT"): 18,   ("AU", "LT"): 12,  ("AT", "LT"): 10,
    ("FI", "LT"): 10,   ("LV", "LT"): 15,  ("EE", "LT"): 8,
    ("NL", "LT"): 40,

    # ── Latvians abroad ──────────────────────────────────────────────────
    ("GB", "LV"): 100,  ("DE", "LV"): 50,  ("IE", "LV"): 32,
    ("SE", "LV"): 32,   ("NO", "LV"): 22,  ("FI", "LV"): 18,
    ("DK", "LV"): 12,   ("AU", "LV"): 8,   ("AT", "LV"): 6,
    ("LT", "LV"): 12,   ("EE", "LV"): 8,   ("NL", "LV"): 20,

    # ── Estonians abroad ─────────────────────────────────────────────────
    ("FI", "EE"): 60,   ("DE", "EE"): 32,  ("SE", "EE"): 28,
    ("GB", "EE"): 22,   ("NO", "EE"): 16,  ("IE", "EE"): 10,
    ("AU", "EE"): 6,    ("AT", "EE"): 5,   ("LV", "EE"): 8,
    ("LT", "EE"): 5,

    # ── Cypriots abroad ──────────────────────────────────────────────────
    ("GB", "CY"): 300,  ("GR", "CY"): 100, ("AU", "CY"): 65,
    ("DE", "CY"): 45,   ("BE", "CY"): 15,  ("SE", "CY"): 10,
    ("FR", "CY"): 10,   ("CH", "CY"): 8,

    # ── Greeks abroad ────────────────────────────────────────────────────
    ("DE", "GR"): 400,  ("AU", "GR"): 350, ("GB", "GR"): 200,
    ("BE", "GR"): 120,  ("CH", "GR"): 100, ("AT", "GR"): 60,
    ("SE", "GR"): 45,   ("CY", "GR"): 100, ("IT", "GR"): 35,
    ("FR", "GR"): 35,   ("NL", "GR"): 30,  ("DK", "GR"): 15,
    ("NO", "GR"): 12,   ("PT", "GR"): 8,   ("IE", "GR"): 8,

    # ── Israelis abroad (Jewish diaspora) ────────────────────────────────
    ("FR", "IL"): 200,  ("DE", "IL"): 200, ("GB", "IL"): 300,
    ("AU", "IL"): 100,  ("BE", "IL"): 55,  ("CH", "IL"): 55,
    ("SE", "IL"): 35,   ("AT", "IL"): 35,  ("IT", "IL"): 45,
    ("GR", "IL"): 10,   ("DK", "IL"): 10,  ("NO", "IL"): 8,

    # ── Finns abroad ─────────────────────────────────────────────────────
    ("SE", "FI"): 300,  ("DE", "FI"): 42,  ("NO", "FI"): 42,
    ("GB", "FI"): 32,   ("AU", "FI"): 22,  ("EE", "FI"): 15,
    ("AT", "FI"): 8,    ("CH", "FI"): 8,

    # ── Swedes abroad ────────────────────────────────────────────────────
    ("NO", "SE"): 100,  ("DK", "SE"): 80,  ("FI", "SE"): 50,
    ("GB", "SE"): 100,  ("DE", "SE"): 55,  ("AU", "SE"): 40,
    ("CH", "SE"): 25,   ("AT", "SE"): 15,  ("BE", "SE"): 12,

    # ── Azerbaijanis abroad ──────────────────────────────────────────────
    ("DE", "AZ"): 80,   ("FR", "AZ"): 35,  ("GB", "AZ"): 35,
    ("IL", "AZ"): 80,   ("GR", "AZ"): 18,  ("RU", "AZ"): 600,
    ("AT", "AZ"): 12,   ("BE", "AZ"): 10,  ("UA", "AZ"): 40,

    # ── Danes abroad ─────────────────────────────────────────────────────
    ("DE", "DK"): 52,   ("SE", "DK"): 35,  ("NO", "DK"): 28,
    ("GB", "DK"): 32,   ("AU", "DK"): 28,  ("CH", "DK"): 10,
    ("AT", "DK"): 8,

    # ── Norwegians abroad ────────────────────────────────────────────────
    ("SE", "NO"): 55,   ("DE", "NO"): 32,  ("GB", "NO"): 42,
    ("AU", "NO"): 55,   ("DK", "NO"): 28,  ("CH", "NO"): 10,
    ("FR", "NO"): 8,    ("AT", "NO"): 6,

    # ── Belgians abroad ──────────────────────────────────────────────────
    ("FR", "BE"): 65,   ("DE", "BE"): 45,  ("GB", "BE"): 32,
    ("CH", "BE"): 22,   ("AU", "BE"): 18,  ("SE", "BE"): 8,
    ("IT", "BE"): 10,   ("PT", "BE"): 8,   ("LU", "BE"): 15,

    # ── Swiss abroad ─────────────────────────────────────────────────────
    ("DE", "CH"): 100,  ("FR", "CH"): 75,  ("IT", "CH"): 55,
    ("GB", "CH"): 32,   ("AU", "CH"): 32,  ("AT", "CH"): 20,
    ("BE", "CH"): 12,   ("SE", "CH"): 8,

    # ── French abroad ────────────────────────────────────────────────────
    ("GB", "FR"): 200,  ("DE", "FR"): 105, ("BE", "FR"): 155,
    ("CH", "FR"): 200,  ("AU", "FR"): 60,  ("IT", "FR"): 40,
    ("SE", "FR"): 15,   ("AT", "FR"): 10,

    # ── Germans abroad ───────────────────────────────────────────────────
    ("CH", "DE"): 310,  ("AT", "DE"): 210, ("GB", "DE"): 205,
    ("AU", "DE"): 105,  ("FR", "DE"): 105, ("SE", "DE"): 55,
    ("BE", "DE"): 40,   ("LU", "DE"): 30,  ("IT", "DE"): 30,
    ("DK", "DE"): 12,

    # ── British abroad ───────────────────────────────────────────────────
    ("AU", "GB"): 1300, ("ES", "GB"): 310, ("FR", "GB"): 205,
    ("DE", "GB"): 105,  ("IE", "GB"): 205, ("MT", "GB"): 55,
    ("GR", "GB"): 25,   ("BE", "GB"): 20,  ("CH", "GB"): 20,
    ("AT", "GB"): 15,   ("IT", "GB"): 15,  ("PT", "GB"): 30,
    ("CY", "GB"): 8,

    # ── Italians abroad ──────────────────────────────────────────────────
    ("DE", "IT"): 650,  ("CH", "IT"): 650, ("GB", "IT"): 410,
    ("FR", "IT"): 385,  ("BE", "IT"): 310, ("AU", "IT"): 255,
    ("AT", "IT"): 105,  ("SE", "IT"): 55,  ("MT", "IT"): 22,
    ("LU", "IT"): 30,   ("GR", "IT"): 10,  ("PT", "IT"): 10,

    # ── Luxembourgish abroad ─────────────────────────────────────────────
    ("DE", "LU"): 32,   ("BE", "LU"): 28,  ("FR", "LU"): 32,
    ("CH", "LU"): 10,   ("AT", "LU"): 5,

    # ── Maltese abroad ───────────────────────────────────────────────────
    ("AU", "MT"): 155,  ("GB", "MT"): 105, ("IT", "MT"): 32,
    ("DE", "MT"): 22,   ("BE", "MT"): 16,  ("CH", "MT"): 8,
    ("SE", "MT"): 5,    ("FR", "MT"): 5,

    # ── San Marinese abroad (near-100% live in Italy) ────────────────────
    ("IT", "SM"): 22,   ("DE", "SM"): 3,   ("GB", "SM"): 2,

    # ── Czech abroad ─────────────────────────────────────────────────────
    ("DE", "CZ"): 72,   ("AT", "CZ"): 55,  ("GB", "CZ"): 55,
    ("CH", "CZ"): 32,   ("SE", "CZ"): 12,  ("AU", "CZ"): 8,
    ("FR", "CZ"): 8,    ("SK", "CZ"): 100,

    # ── Portuguese abroad ────────────────────────────────────────────────
    ("FR", "PT"): 600,  ("DE", "PT"): 310, ("CH", "PT"): 210,
    ("GB", "PT"): 205,  ("LU", "PT"): 105, ("BE", "PT"): 55,
    ("NO", "PT"): 32,   ("SE", "PT"): 32,  ("AU", "PT"): 25,
    ("IT", "PT"): 20,   ("GR", "PT"): 8,

    # ── Spanish abroad (Spain not competing in 2026, but votes) ─────────
    # included for completeness when Spain is a voter
    ("FR", "ES"): 310,  ("DE", "ES"): 205, ("GB", "ES"): 105,
    ("CH", "ES"): 80,   ("BE", "ES"): 55,  ("AU", "ES"): 30,
    ("IT", "ES"): 25,   ("SE", "ES"): 15,  ("AT", "ES"): 12,

    # ── Dutch abroad (Netherlands not competing in 2026, but votes) ──────
    ("DE", "NL"): 150,  ("GB", "NL"): 80,  ("BE", "NL"): 50,
    ("AU", "NL"): 40,   ("FR", "NL"): 25,  ("CH", "NL"): 20,
    ("AT", "NL"): 10,   ("SE", "NL"): 8,

    # ── Irish abroad ─────────────────────────────────────────────────────
    ("GB", "IE"): 800,  ("AU", "IE"): 100, ("DE", "IE"): 30,
    ("FR", "IE"): 20,   ("SE", "IE"): 10,  ("CH", "IE"): 8,

    # ── Australians abroad (Australian diaspora in Europe) ───────────────
    ("GB", "AU"): 80,   ("DE", "AU"): 15,  ("FR", "AU"): 12,
    ("IT", "AU"): 8,    ("GR", "AU"): 8,   ("SE", "AU"): 5,
}

# Pre-compute the global max log-diaspora for normalisation
_MAX_LOG = math.log10(max(DIASPORA_K.values()) + 1)


def diaspora_score(voter_cc: str, performer_cc: str) -> float:
    """
    Normalised diaspora score [0, 1].
    1.0 = largest known diaspora (Ukrainians in Germany ~1.5M post-2022).
    0.0 = no known diaspora community.
    """
    raw = DIASPORA_K.get((voter_cc, performer_cc), 0.0)
    if raw == 0:
        return 0.0
    return math.log10(raw + 1) / _MAX_LOG


if __name__ == "__main__":
    # Quick sanity check: top 20 bilateral diaspora pairs
    pairs = sorted(DIASPORA_K.items(), key=lambda x: -x[1])
    print(f"{'Voter':<6} {'Performer':<12} {'Thousands':>12} {'Score':>8}")
    print("-" * 44)
    for (v, p), k in pairs[:25]:
        print(f"  {v:<4} → {p:<10} {k:>10.0f}k  {diaspora_score(v, p):>7.3f}")
