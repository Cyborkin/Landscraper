# Landscraper: Data Source Registry

## Validation Summary

- **Sources from Gemini:** 26 across 6 categories
- **Sources verified via web research:** 8/10 top sources checked
- **Sources flagged with discrepancies:** 4 (see Flagged section)
- **Novel sources added:** 4 (data.colorado.gov, DRCOG, Boulder Open Data, DOLA)

---

## Tier 1: High-Confidence Sources (verified, accessible, reliable)

These sources were web-verified as publicly accessible with actionable data.

| Source | URL | Data Type | Access Method | Complexity | Frequency | Coverage | Quality | Validation Notes |
|--------|-----|-----------|---------------|------------|-----------|----------|---------|------------------|
| PPRBD (El Paso) | [pprbd.org](https://www.pprbd.org/) | Building Permits | Public search | Moderate (jQuery/Bootstrap/Infragistics) | Real-time | El Paso County, Colorado Springs, Monument, etc. | 5 | Verified. Public search works. No API despite Gemini's claim — scrape via httpx + BS4 or Playwright |
| Census Bureau BPS | [census.gov/construction/bps](https://www.census.gov/construction/bps/index.html) | Permit Survey (aggregate) | CSV/Excel download | Low (static files) | Monthly (17th workday) | County-level nationwide | 5 | Verified. CSV/Excel downloads, NOT a JSON API. Good for trend baselines |
| DWR Well Permits | [dwr.state.co.us/Tools/WellPermits](https://dwr.state.co.us/Tools/WellPermits) | Water well permits | Public guest search | Moderate (search form + grid) | Daily | All CO counties | 4 | Verified. Guest access, county filter, rich fields (depth, yield, coordinates). Leading indicator for rural development |
| Denver Legistar | [denver.legistar.com](https://denver.legistar.com/Calendar.aspx) | Municipal agendas/minutes | Public web + iCal export | Low-Moderate | Bi-weekly | Denver | 4 | Verified. General municipal calendar — filter for "Community Planning and Housing" committee. iCal export, no RSS |
| data.colorado.gov | [Building Permit Counts](https://data.colorado.gov/Building-and-Facilities/Building-Permit-Counts-in-Colorado/v4as-sthd) | Aggregate permit counts | Socrata SODA API | Low (REST API) | Varies | Statewide by jurisdiction | 4 | **NOVEL** — Gemini missed this. Socrata provides JSON API with SoQL queries. County/city granularity |
| SEC EDGAR | [sec.gov/edgar](https://www.sec.gov/edgar/search/) | Homebuilder 10-K/Q filings | REST API (JSON) | Low | Quarterly | National/Regional | 3 | Gemini verified. Search for Lennar, DR Horton, KB Home regional CapEx disclosures |
| BizWest | [bizwest.com/real-estate](https://bizwest.com/category/real-estate-construction/) | News/project announcements | RSS | Low | Daily | Northern Colorado | 4 | Not individually verified but RSS is standard for news sites |

## Tier 2: Accessible but Requires Authentication or Registration

| Source | URL | Data Type | Access Method | Complexity | Frequency | Coverage | Quality | Validation Notes |
|--------|-----|-----------|---------------|------------|-----------|----------|---------|------------------|
| Denver e-Permits | [denvergov.org/epermits](https://www.denvergov.org/epermits) | Building Permits | Auth required | High (Azure B2C + JS) | Daily | Denver County | 5 (data quality), 2 (accessibility) | Requires login. Gemini listed as "Public Website" — INCORRECT. Need account to search permits |
| Arapahoe Accela | [aca-prod.accela.com/ARAPAHOE](https://aca-prod.accela.com/ARAPAHOE/Default.aspx) | Permits | Registration required | High (Accela JS, session-heavy) | Daily | Arapahoe County | 4 | As of 9/16/2025, search requires registered account. Free registration available |
| Jeffco Citizen Portal | [planning.jeffco.us](https://planning.jeffco.us/citizenportal) | Permits/Planning | Registration required | High (Auth + JS) | Daily | Jefferson County | 4 | Not individually verified. Gemini noted registration requirement |
| Larimer Community Dev | [onlineportal.larimer.org](https://onlineportal.larimer.org/v3/customer/login) | Permits | CSS portal login | High (JS portal) | Daily | Larimer County | 4 | URL suggests login required |
| Broomfield Citizen Access | [broomfield.org](https://www.broomfield.org/263/Building) | Permits | Accela portal | High (Accela JS) | Daily | Broomfield County | 4 | Not individually verified. Accela sites typically require registration |
| DORA Electrical/Plumbing | [dora.colorado.gov](https://dora.colorado.gov/professions-and-occupations/electrical-and-plumbing-permits) | Trade permits | Public search portal | High | Daily | Statewide | 5 | Late-stage indicator. Not individually verified |
| REcolorado | [recolorado.com](https://www.recolorado.com) | MLS new construction listings | Public website (JS) | Moderate | Real-time | Denver Metro | 5 | MLS data. Anti-scraping likely. Consider IDX feed partnership |
| Douglas Building | [douglas.co.us/building](https://www.douglas.co.us/building-division/online-services/) | Permits | Public website | Moderate | Daily | Douglas County | 5 | High-growth county. Not individually verified |
| Weld E-Permit | [weld.gov/epermit](https://www.weld.gov/Government/Departments/Building/E-Permit-Center) | Permits | Public website | Moderate | Daily | Weld County | 5 | Highest-growth county. Not individually verified |
| Boulder County Permits | [bouldercounty.org](https://www.bouldercounty.org/property-and-land/land-use/building/permit-records/) | Permits | Public website | Moderate | Daily | Unincorp. Boulder | 4 | Not individually verified |

## Tier 3: Experimental / Novel Indicators

| Source | URL | Data Type | Access Method | Complexity | Frequency | Coverage | Quality | Validation Notes |
|--------|-----|-----------|---------------|------------|-----------|----------|---------|------------------|
| DRCOG Regional Data Catalog | [data.drcog.org](https://data.drcog.org/) | GIS, land use, aerial imagery, growth models | Open data portal | Moderate (GIS downloads) | Varies | Denver Metro (9 counties) | 4 | **NOVEL** — Gemini missed. UrbanSim growth model, biannual aerial photography, land use data |
| Boulder County Open Data | [opendata-bouldercounty.hub.arcgis.com](https://opendata-bouldercounty.hub.arcgis.com/) | Parcels, zoning, building footprints | ArcGIS Hub | Moderate (GeoJSON/API) | Continuous from permits | Boulder County | 4 | **NOVEL** — building footprints updated from permit records |
| DOLA/Division of Housing | [cdola.colorado.gov](https://cdola.colorado.gov/) | Housing development tracking, funding approvals | Public website | Moderate | Varies | Statewide | 3 | **NOVEL** — tracks affordable housing development funding ($68M+ in H1 2025) |
| Colorado Geological Survey | [coloradogeologicalsurvey.org](https://coloradogeologicalsurvey.org/land-use/) | Geotechnical reviews | Public search | Moderate | As-filed | Statewide | 4 | State law requires geo reviews for subdivisions. Early signal of developer intent |
| School District Projections | [svvsd.org](https://www.svvsd.org/departments/planning/), [sd27j.org](https://www.sd27j.org/domain/56) | Enrollment projections, development yield maps | Public website/PDF | Moderate (PDF parsing) | Annual | District-specific | 5 | 27J (Brighton/Thornton) publishes GIS maps of future student yield from approved developments |
| DWR Water Rights Transactions | [dwr.state.co.us](https://dwr.state.co.us/Tools/WaterRights/Transactions) | Water rights changes | Public search | Moderate | As-filed | Division 1 (South Platte) | 4 | Large developments require "Change of Water Right" cases years before building |
| Denver Water Construction | [denverwater.org/construction](https://www.denverwater.org/construction) | Main extensions | Map/PDF | High (ArcGIS/PDF) | Weekly | Denver Metro | 4 | Physical infrastructure indicator. Not verified |
| Broadband CO | [broadband.colorado.gov](https://broadband.colorado.gov/) | Fiber expansion maps | ArcGIS | High (GIS service) | Quarterly | Statewide | 3 | Greenfield fiber digging may precede residential permits by 6 months |
| CDOT OTIS | [otis.dot.state.co.us](https://otis.dot.state.co.us/) | Road/infrastructure projects | Map portal | High (ArcGIS) | Monthly | Front Range | 3 | Road projects near developments. Not verified |
| Lennar Communities | [lennar.com/colorado](https://www.lennar.com/new-homes/colorado/denver) | Builder community maps | Public website (JS) | Moderate | Weekly | Front Range | 4 | Direct builder intelligence. Repeat for DR Horton, KB Home, etc. |

## Flagged / Discrepancies from Gemini's Research

| Source | Gemini's Claim | Actual Finding | Impact |
|--------|----------------|----------------|--------|
| PPRBD (El Paso) | "Excellent API" | No API found. jQuery/Bootstrap/Infragistics grid. Public search only | Must use scraping, not API calls |
| Census BPS | "Low (JSON API)" | CSV/Excel file downloads only. No API | Need file download + parse pipeline, not API client |
| Denver e-Permits | "Public Website" | Requires Azure B2C authentication | Can't scrape without account. May violate ToS |
| Arapahoe Accela | "Public Website" | Registration required for search since 9/2025 | Free registration needed. May trigger anti-bot |
| Adams County Accela | URL listed as epermits.adcogov.org | Connection refused (ECONNREFUSED) | URL may have changed or service may be down |

## POC Priority Order

Recommended implementation order for collection specialists, balancing value and complexity:

### Sprint 1: Quick Wins (Low complexity, high value)
1. **Census BPS** — CSV download + parse. County-level baselines. Immediate trend data
2. **data.colorado.gov SODA API** — REST API, no scraping needed. Aggregate permit counts
3. **Legistar RSS/iCal** — Multiple cities. Planning meeting agendas as early signals
4. **SEC EDGAR** — REST API. Quarterly homebuilder regional CapEx data
5. **BizWest RSS** — Standard RSS parsing. Northern CO project announcements

### Sprint 2: Core Permit Scraping (Moderate complexity, highest value)
6. **PPRBD (El Paso)** — Best public access of all county portals. jQuery/Infragistics grid
7. **Weld County** — Highest growth county. Verify portal accessibility
8. **Douglas County** — High growth. Verify portal accessibility
9. **DWR Well Permits** — Public guest access, leading indicator for rural development

### Sprint 3: Auth-Required Portals (High complexity)
10. **Arapahoe Accela** — Register account, handle sessions
11. **Denver e-Permits** — Need account creation. Evaluate ToS
12. **Jeffco/Larimer/Boulder/Broomfield** — Various auth portals

### Sprint 4: Novel Indicators
13. **School district projections** — PDF parsing, annual
14. **Colorado Geological Survey** — Geotechnical reviews
15. **DWR Water Rights** — Water court filings
16. **DRCOG aerial imagery** — Change detection via satellite/aerial comparison
