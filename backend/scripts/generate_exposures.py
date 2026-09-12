from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DATA = Path(__file__).resolve().parents[2] / "data"
RNG = np.random.default_rng(4711)

NAMES = [
    ("Meridian Aviation", "Aviation"), ("Starhaven Finserv", "Housing finance"),
    ("Kanaka Gems & Exports", "Gems and jewellery"), ("Trinetra Infra Holdings", "Infrastructure"),
    ("Vaidya Agro Commodities", "Agri commodities"), ("Sahyadri Steelworks", "Steel"),
    ("Orchid Realty Projects", "Real estate"), ("Bluecrest Logistics", "Logistics"),
    ("Anantam Power Systems", "Power"), ("Nilgiri Textile Mills", "Textiles"),
    ("Kaveri Cements", "Cement"), ("Pushpak Shipping", "Shipping"),
    ("Zenith Pharma Labs", "Pharmaceuticals"), ("Marudhar Sugar Mills", "Sugar"),
    ("Chandrika Hotels", "Hospitality"), ("Ravindra Auto Components", "Auto ancillary"),
    ("Ashwamedh Constructions", "Construction"), ("Suryakiran Solar", "Renewables"),
    ("Neelkanth Ceramics", "Ceramics"), ("Girnar Paper Mills", "Paper"),
    ("Vasudha Seeds", "Agri inputs"), ("Tamrapatra Metals", "Metals"),
    ("Harit Fertilisers", "Fertilisers"), ("Indraprastha Malls", "Retail property"),
    ("Konark Marine Foods", "Seafood"), ("Samvara Electricals", "Electricals"),
    ("Bhargava Diagnostics", "Healthcare"), ("Utkal Mining Corp", "Mining"),
    ("Palash Petrochem", "Petrochemicals"), ("Rudraksh Engineering", "Engineering"),
    ("Saptagiri Poultry", "Poultry"), ("Vindhya Coal Traders", "Coal trading"),
    ("Amaravati Housing", "Housing"), ("Devgiri Roadways", "Transport"),
    ("Kailash Plastics", "Plastics"), ("Manjira Dairy", "Dairy"),
    ("Sonepur Sponge Iron", "Shipbuilding"), ("Barhampur Tea Estates", "Plantations"),
    ("Nakshatra Media", "Media"), ("Varuna Water Systems", "Water treatment"),
    ("Ekaksh Semiconductors", "Electronics"), ("Gopalpur Port Services", "Ports"),
    ("Hemadri Granites", "Stone"), ("Ishwar Packaging", "Packaging"),
    ("Jalaram Edible Oils", "Edible oils"), ("Kritika Apparel", "Apparel"),
    ("Lohit Wires", "Wires and cables"), ("Mrinal Chemicals", "Chemicals"),
    ("Nandan Warehousing", "Warehousing"), ("Omkar Rubber", "Rubber"),
    ("Prabhat Glass", "Glass"), ("Quila Heritage Resorts", "Hospitality"),
    ("Rachana Furniture", "Furniture"), ("Shilpa Foundry", "Foundry"),
    ("Tejaswi Renewables", "Renewables"), ("Ujjwal Printing", "Printing"),
    ("Vasant Vihar Estates", "Real estate"), ("Yamunotri Pipes", "Pipes"),
    ("Zaheerabad Spirits", "Distilleries"), ("Aravali Mineral Water", "Beverages"),
    ("Rivergate Housing Finance", "Housing finance"), ("Altair Airways", "Aviation"),
    ("Pradhan Housing Capital", "Housing finance"), ("Belmont Diamond Trading", "Gems and jewellery"),
    ("Corvine Marine Yards", "Shipbuilding"),
]

ARCHETYPES = {
    "collateral_erosion": dict(
        collateral_cover=(0.35, 0.65), collateral_change_12m=(-0.72, -0.34),
        dscr=(0.55, 0.95), ebitda_change_12m=(-0.45, -0.08), restructure_count=(1, 2),
        disbursal_sweep_pct=(0.05, 0.28), related_party_share=(0.02, 0.16),
        unsecured_growth_12m=(0.1, 0.7), promoter_pledge_pct=(0.6, 0.95), dpd=(30, 180)),
    "related_party_funnel": dict(
        collateral_cover=(0.7, 1.3), collateral_change_12m=(-0.2, 0.05),
        dscr=(0.8, 1.4), ebitda_change_12m=(-0.2, 0.2), restructure_count=(0, 1),
        disbursal_sweep_pct=(0.55, 0.92), related_party_share=(0.42, 0.88),
        unsecured_growth_12m=(1.6, 7.5), promoter_pledge_pct=(0.3, 0.8), dpd=(0, 45)),
    "serial_restructure": dict(
        collateral_cover=(0.6, 1.0), collateral_change_12m=(-0.35, -0.05),
        dscr=(0.6, 1.05), ebitda_change_12m=(-0.4, -0.02), restructure_count=(2, 4),
        disbursal_sweep_pct=(0.05, 0.3), related_party_share=(0.05, 0.25),
        unsecured_growth_12m=(0.6, 2.2), promoter_pledge_pct=(0.45, 0.9), dpd=(45, 210)),
    "watchlist": dict(
        collateral_cover=(0.85, 1.3), collateral_change_12m=(-0.26, 0.02),
        dscr=(0.92, 1.4), ebitda_change_12m=(-0.2, 0.12), restructure_count=(0, 2),
        disbursal_sweep_pct=(0.08, 0.42), related_party_share=(0.08, 0.36),
        unsecured_growth_12m=(0.7, 2.3), promoter_pledge_pct=(0.42, 0.86), dpd=(0, 80)),
    "standard": dict(
        collateral_cover=(1.25, 2.4), collateral_change_12m=(-0.08, 0.16),
        dscr=(1.4, 3.1), ebitda_change_12m=(-0.05, 0.3), restructure_count=(0, 0),
        disbursal_sweep_pct=(0.01, 0.18), related_party_share=(0.0, 0.14),
        unsecured_growth_12m=(0.0, 0.6), promoter_pledge_pct=(0.0, 0.4), dpd=(0, 5)),
}

CASE_MODELS = {
    "Meridian Aviation": dict(
        modelled_on="kingfisher", pattern="Single dominant intangible pledged as collateral, revalued down while the debt stayed fixed",
        exposure_cr=9000.0, collateral_cover=0.41, collateral_change_12m=-0.68, dscr=0.62,
        ebitda_change_12m=-0.31, restructure_count=2, disbursal_sweep_pct=0.18,
        related_party_share=0.11, unsecured_growth_12m=0.9, promoter_pledge_pct=0.91, days_past_due=150),
    "Starhaven Finserv": dict(
        modelled_on="rhfl", pattern="General purpose corporate loan book grew roughly nine times in one year, to borrowers reclassified out of related-party status",
        exposure_cr=7900.0, collateral_cover=0.92, collateral_change_12m=-0.14, dscr=1.02,
        ebitda_change_12m=-0.06, restructure_count=1, disbursal_sweep_pct=0.81,
        related_party_share=0.63, unsecured_growth_12m=7.8, promoter_pledge_pct=0.58, days_past_due=25),
    "Kanaka Gems & Exports": dict(
        modelled_on="pnb_lou", pattern="Guarantees issued off the core banking system against no sanctioned limit, rolled over for years",
        exposure_cr=14360.0, collateral_cover=0.34, collateral_change_12m=-0.21, dscr=0.71,
        ebitda_change_12m=-0.12, restructure_count=1, disbursal_sweep_pct=0.88,
        related_party_share=0.57, unsecured_growth_12m=3.4, promoter_pledge_pct=0.66, days_past_due=95),
    "Amaravati Housing": dict(
        modelled_on="dhfl", pattern="Bulk of the book disbursed to dozens of entities connected to the promoters, with funds round-tripped back",
        exposure_cr=34620.0, collateral_cover=0.78, collateral_change_12m=-0.19, dscr=0.88,
        ebitda_change_12m=-0.22, restructure_count=1, disbursal_sweep_pct=0.74,
        related_party_share=0.68, unsecured_growth_12m=2.6, promoter_pledge_pct=0.72, days_past_due=70),
    "Sonepur Sponge Iron": dict(
        modelled_on="abg", pattern="Drawdowns diverted over five years to buy assets for related parties, found only by forensic audit",
        exposure_cr=22840.0, collateral_cover=0.52, collateral_change_12m=-0.44, dscr=0.64,
        ebitda_change_12m=-0.37, restructure_count=3, disbursal_sweep_pct=0.69,
        related_party_share=0.61, unsecured_growth_12m=1.9, promoter_pledge_pct=0.83, days_past_due=200),
    "Rivergate Housing Finance": dict(
        modelled_on="rhfl", pattern="Lending book expanded far faster than the business, to thinly capitalised related borrowers",
        exposure_cr=2410.0, collateral_cover=0.88, collateral_change_12m=-0.11, dscr=1.06,
        ebitda_change_12m=-0.04, restructure_count=0, disbursal_sweep_pct=0.66,
        related_party_share=0.51, unsecured_growth_12m=5.2, promoter_pledge_pct=0.49, days_past_due=10),
    "Altair Airways": dict(
        modelled_on="kingfisher", pattern="Security cover concentrated in one intangible asset, written down while debt held flat",
        exposure_cr=3140.0, collateral_cover=0.47, collateral_change_12m=-0.55, dscr=0.74,
        ebitda_change_12m=-0.26, restructure_count=2, disbursal_sweep_pct=0.14,
        related_party_share=0.09, unsecured_growth_12m=1.1, promoter_pledge_pct=0.84, days_past_due=120),
    "Pradhan Housing Capital": dict(
        modelled_on="dhfl", pattern="Large share of disbursals to entities connected to the promoter group, funds cycled back",
        exposure_cr=11780.0, collateral_cover=0.81, collateral_change_12m=-0.16, dscr=0.94,
        ebitda_change_12m=-0.18, restructure_count=1, disbursal_sweep_pct=0.71,
        related_party_share=0.59, unsecured_growth_12m=2.1, promoter_pledge_pct=0.63, days_past_due=55),
    "Belmont Diamond Trading": dict(
        modelled_on="pnb_lou", pattern="Trade guarantees rolled over repeatedly without appearing in the lender's own exposure reporting",
        exposure_cr=4820.0, collateral_cover=0.39, collateral_change_12m=-0.18, dscr=0.79,
        ebitda_change_12m=-0.09, restructure_count=1, disbursal_sweep_pct=0.83,
        related_party_share=0.48, unsecured_growth_12m=2.9, promoter_pledge_pct=0.57, days_past_due=65),
    "Corvine Marine Yards": dict(
        modelled_on="abg", pattern="Drawdowns routed to group entities over several years, visible only on forensic review",
        exposure_cr=6340.0, collateral_cover=0.58, collateral_change_12m=-0.38, dscr=0.69,
        ebitda_change_12m=-0.29, restructure_count=2, disbursal_sweep_pct=0.62,
        related_party_share=0.55, unsecured_growth_12m=1.7, promoter_pledge_pct=0.77, days_past_due=145),
}

MIX = (["collateral_erosion"] * 5 + ["related_party_funnel"] * 5 + ["serial_restructure"] * 6
       + ["watchlist"] * 16 + ["standard"] * 33)


def u(lo, hi):
    return float(RNG.uniform(lo, hi))


def series(months: int, start: float, drift: float, noise: float) -> list[float]:
    out, v = [], start
    for _ in range(months):
        v = max(0.02, v * (1 + drift + RNG.normal(0, noise)))
        out.append(round(v, 3))
    return out


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    order = list(MIX)
    RNG.shuffle(order)
    rows = []
    for i, ((name, sector), arch) in enumerate(zip(NAMES, order), start=1):
        m = CASE_MODELS.get(name)
        if m:
            row = dict(exposure_id=f"EXP{i:03d}", entity=name, sector=sector,
                       archetype="case_modelled", modelled_on=m["modelled_on"],
                       pattern=m["pattern"],
                       **{k: v for k, v in m.items() if k not in ("modelled_on", "pattern")})
            row["collateral_cr"] = round(row["exposure_cr"] * row["collateral_cover"], 1)
            row["vintage_months"] = int(RNG.integers(60, 190))
            row["collateral_series"] = series(
                24, row["collateral_cover"] / (1 + row["collateral_change_12m"]),
                row["collateral_change_12m"] / 24, 0.03)
            row["debt_series"] = series(24, 1.0, 0.004, 0.01)
            rows.append(row)
            continue

        a = ARCHETYPES[arch]
        exposure = float(round(np.exp(RNG.uniform(np.log(85), np.log(9200))), -1))
        cover = u(*a["collateral_cover"])
        chg = u(*a["collateral_change_12m"])
        rows.append(dict(
            exposure_id=f"EXP{i:03d}",
            entity=name,
            sector=sector,
            archetype=arch,
            modelled_on=None,
            pattern=None,
            exposure_cr=exposure,
            collateral_cr=round(exposure * cover, 1),
            collateral_cover=round(cover, 3),
            collateral_change_12m=round(chg, 3),
            dscr=round(u(*a["dscr"]), 2),
            ebitda_change_12m=round(u(*a["ebitda_change_12m"]), 3),
            restructure_count=int(RNG.integers(a["restructure_count"][0], a["restructure_count"][1] + 1)),
            disbursal_sweep_pct=round(u(*a["disbursal_sweep_pct"]), 3),
            related_party_share=round(u(*a["related_party_share"]), 3),
            unsecured_growth_12m=round(u(*a["unsecured_growth_12m"]), 2),
            promoter_pledge_pct=round(u(*a["promoter_pledge_pct"]), 3),
            days_past_due=int(RNG.integers(*a["dpd"]) if a["dpd"][1] > a["dpd"][0] else 0),
            vintage_months=int(RNG.integers(14, 190)),
            collateral_series=series(24, cover / (1 + chg), chg / 24, 0.035),
            debt_series=series(24, 1.0, 0.004, 0.012),
        ))
    (DATA / "exposures.json").write_text(json.dumps(rows, indent=1))
    total = sum(r["exposure_cr"] for r in rows)
    print(f"exposures       {len(rows)}")
    print(f"total exposure  Rs {total:,.0f} crore")
    from collections import Counter
    for k, v in Counter(r["archetype"] for r in rows).most_common():
        print(f"  {k:<22} {v}")


if __name__ == "__main__":
    main()
