# Verified Data Sources for Colorado Front Range Development Intelligence

**Research Date:** 2026-03-06
**Methodology:** Every URL below was fetched and data returned was inspected. No theoretical sources.

---

## Summary

| Category | Sources Found | Verified Working |
|----------|--------------|-----------------|
| ArcGIS Feature Services (city open data) | 5 | 5 |
| REST/JSON APIs (government) | 4 | 4 |
| Socrata SODA APIs | 2 | 2 |
| RSS/Atom Feeds (news) | 3 | 3 |
| CSV Downloads (no API key) | 2 | 2 |
| **Total NEW sources** | **16** | **16** |

---

## 1. Denver Residential Construction Permits (ArcGIS Feature Service)

**Status: VERIFIED WORKING**

- **URL:** `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316`
- **Hub Page:** https://opendata-geospatialdenver.hub.arcgis.com/datasets/residential-construction-permits
- **Format:** ArcGIS REST API (JSON, GeoJSON)
- **Records:** 77,324 residential construction permits
- **Update Frequency:** Ongoing (extracted from Accela database)
- **Coverage:** City and County of Denver
- **Key Fields:** `PERMIT_NUM`, `DATE_ISSUED`, `ADDRESS`, `CLASS` (New Building / Alteration / Tenant Finish), `VALUATION`, `PERMIT_FEE`, `CONTRACTOR_NAME`, `UNITS`, `NEIGHBORHOOD`, `SCHEDNUM` (parcel), `DATE_RECEIVED`, `FINAL_DATE`, coordinates
- **Why it matters:** Individual permit-level data with valuations and geocoded locations. The `CLASS` field lets us filter for "New Building" permits specifically. Not previously in our registry.

**Sample curl:**
```bash
curl -s "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316/query?where=CLASS='New Building'&outFields=PERMIT_NUM,DATE_ISSUED,ADDRESS,CLASS,VALUATION,CONTRACTOR_NAME,NEIGHBORHOOD,UNITS&resultRecordCount=10&f=json&orderByFields=OBJECTID+DESC"
```

**Sample record (returned 2026-03-06):**
```
PERMIT_NUM: 2026-RESCON-0000356
ADDRESS: 2917 W 28th AVE
CLASS: New Building
VALUATION: 26811
CONTRACTOR_NAME: AFFORDABLE GARAGES & CONCRETE LLC
NEIGHBORHOOD: Jefferson Park
```

---

## 2. Denver Zone Map Amendments / Rezoning (ArcGIS Feature Service)

**Status: VERIFIED WORKING**

- **URL:** `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ZONE_MAPAMENDMENTS_A/FeatureServer/356`
- **Format:** ArcGIS REST API (JSON, GeoJSON) - polygon geometries
- **Coverage:** City and County of Denver
- **Key Fields:** `APP_NUM`, `APP_DATE`, `STATUS`, `FROM_ZONE_DESC`, `ZONE_DESCRIPTION`, `ZONE_DISTRICT`, `ZONE_DIST_TYPE` (Residential/Commercial), `NBHD`, `COUNCIL_DIST`, `ACRES`, `HEIGHT_STORIES`, `ADU`, `NBHD_CONTEXT` (Suburban/Urban Edge)
- **Why it matters:** Rezoning is a LEADING indicator -- it happens before permits are issued. A parcel rezoned from single-unit to multi-unit signals upcoming development. The `ACRES` and `HEIGHT_STORIES` fields quantify development scale.

**Sample curl:**
```bash
curl -s "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ZONE_MAPAMENDMENTS_A/FeatureServer/356/query?where=STATUS='Pending'&outFields=APP_NUM,APP_DATE,FROM_ZONE_DESC,ZONE_DESCRIPTION,ZONE_DIST_TYPE,NBHD,ACRES,HEIGHT_STORIES&f=json&orderByFields=OBJECTID+DESC&resultRecordCount=10"
```

---

## 3. Denver Demolition Permits (ArcGIS Feature Service)

**Status: VERIFIED WORKING**

- **URL:** `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_DEMOLITIONPERMIT_P/FeatureServer/318`
- **Format:** ArcGIS REST API (JSON)
- **Records:** 9,465 demolition permits
- **Coverage:** City and County of Denver
- **Why it matters:** Demolition permits are a precursor to new construction, especially in infill areas. Cross-reference with rezoning data for redevelopment detection.

**Sample curl:**
```bash
curl -s "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_DEMOLITIONPERMIT_P/FeatureServer/318/query?where=1=1&outFields=*&resultRecordCount=5&f=json&orderByFields=OBJECTID+DESC"
```

---

## 4. Denver Additional Services (Same ArcGIS Org)

**Status: VERIFIED ACCESSIBLE** (org ID: `zdB7qR0BtYrg0Xpl`)

All at `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/{NAME}/FeatureServer`:

| Service Name | What It Is |
|---|---|
| `ODC_DEV_COMMERCIALCONSTPERMIT_P` | Commercial construction permits |
| `ODC_ENG_DEVELOPMENTSERVICESPROJ_P` | Development services projects |
| `ODC_ZONE_ZONING_A` (Layer 209) | Current zoning districts |
| `ODC_PLAN_SITEDEVPLANS_A` | Site development plans |
| `ODC_PLAN_DESIGNREVIEWDISTS_A` | Design review districts |
| `ODC_PLAN_EXISTINGLANDUSE_A` | Existing land use |
| `AffordableHousingMap_WFL1` | Affordable housing locations |
| `Middle_Housing_Stock` | Middle housing stock inventory |
| `ODC_residential_rental_property_active_licenses` | Active rental property licenses |

---

## 5. Fort Collins Building Permits (ArcGIS Feature Service + Socrata)

**Status: VERIFIED WORKING (both endpoints)**

### ArcGIS Endpoint
- **URL:** `https://services1.arcgis.com/dLpFH5mwVvxSN4OE/arcgis/rest/services/Building_Permits/FeatureServer/0`
- **Records:** 2,078 current permits
- **Key Fields:** `PERMITNUM`, `PERMITTYPE`, `B1_APPL_STATUS`, `B1_WORK_DESC`, `SUBDIVISIONNAME`, `MATCH_ADDR`, `B1_PER_GROUP`, coordinates, `WEB` (link to Accela detail page)
- **Coverage:** City of Fort Collins (Larimer County)

### Socrata Endpoint
- **URL:** `https://opendata.fcgov.com/resource/fvgz-viez.json`
- **Format:** Socrata SODA API (JSON, CSV, GeoJSON)
- **Key Fields:** Same as ArcGIS plus GeoJSON `the_geom` for spatial queries
- **Coverage:** City of Fort Collins

**Sample curl (Socrata):**
```bash
curl -s "https://opendata.fcgov.com/resource/fvgz-viez.json?\$limit=10&\$order=:id+DESC"
```

**Sample curl (ArcGIS):**
```bash
curl -s "https://services1.arcgis.com/dLpFH5mwVvxSN4OE/arcgis/rest/services/Building_Permits/FeatureServer/0/query?where=PERMITTYPE='New Single Family'&outFields=PERMITNUM,PERMITTYPE,B1_WORK_DESC,MATCH_ADDR,SUBDIVISIONNAME&resultRecordCount=10&f=json"
```

---

## 6. Aurora Building Permits + Active Development Applications (ArcGIS MapServer)

**Status: VERIFIED WORKING**

### Building Permits (1-Month rolling window)
- **URL:** `https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/157`
- **Records:** ~1,259 permits in current 1-month window
- **Key Fields:** `Permit_`, `FolderType`, `FolderDesc`, `FolderGroupDesc`, `SubDesc`, `FolderDescription` (detailed scope), `FolderCondition`, `IssueDate`, `InDate`, `valuation`, `Address`, `PropertyRoll` (parcel ID), coordinates
- **Coverage:** City of Aurora (Adams/Arapahoe Counties)

### Additional Aurora Layers on same MapServer:
| Layer | ID | Description |
|---|---|---|
| Building Permits (all) | 44 | Full permit history |
| Building Permits (6 months) | 156 | 6-month rolling window |
| Building Permits (1 month) | 157 | 1-month rolling window |
| **Active Development Applications** | **180** | **Current planning/zoning applications** |
| Building Inspections | 181 | Inspection records |
| Public Improvement Permits | 182 | Infrastructure permits |
| Master Plans | 24 | Master plan areas |
| Neighborhood Plans | 276 | Neighborhood plans |

### Active Development Applications (Layer 180) -- HIGH VALUE
- **Key Fields:** `DANum`, `FolderName`, `folderdescription`, `FolderStatus`, `Address`, `Parcel`, `SiteAcreage`, `PropNumLots`, `PropNumDwell`, `ExistZone`, `PropZone`, `ZoneReZone`, `GDPNew`, `FDPNew`, `SubPlatNew`, `CondUse`, `CaseMan`
- **Why it matters:** Shows CURRENT development applications with proposed zoning changes, number of proposed lots/dwellings, and acreage. This is one of the richest planning-stage datasets found.

**Sample curl (Active Dev Applications):**
```bash
curl -s "https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/180/query?where=1=1&outFields=DANum,FolderName,folderdescription,FolderStatus,Address,SiteAcreage,PropNumLots,PropNumDwell,ExistZone,PropZone&resultRecordCount=10&f=json&orderByFields=OBJECTID+DESC"
```

---

## 7. FRED Building Permits Time Series (CSV, No API Key Required)

**Status: VERIFIED WORKING**

Federal Reserve Economic Data provides monthly building permits data via direct CSV download. No API key is needed for the CSV endpoint.

| Series ID | Coverage | Latest Data |
|---|---|---|
| `DENV708BPPRIV` | Denver-Aurora-Lakewood MSA (total) | Through Dec 2025 |
| `DENV708BP1FH` | Denver-Aurora-Lakewood MSA (single-family) | Through Dec 2025 |
| `COBPPRIV` | Colorado statewide | Through Dec 2025 |
| `COLO808BPPRIV` | Colorado Springs MSA | Through Dec 2025 |
| `GREE508BPPRIV` | Greeley MSA (Weld County) | Through Dec 2025 |
| `BPPRIV008013` | Boulder County | Through 2024 (annual) |

- **Format:** CSV with columns `observation_date` and value
- **Update Frequency:** Monthly (released ~4-6 weeks after reference month)
- **Why it matters:** Free, no-auth, machine-readable trend data. Perfect for scoring model baselines and market cycle detection.

**Sample curl:**
```bash
# Denver MSA monthly permits, last 12 months
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DENV708BPPRIV&cosd=2025-01-01&coed=2026-12-31"

# Colorado statewide
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=COBPPRIV&cosd=2025-01-01&coed=2026-12-31"

# Multiple series in one call
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DENV708BPPRIV,COLO808BPPRIV,GREE508BPPRIV&cosd=2025-01-01&coed=2026-12-31"
```

---

## 8. DOLA State Demography Office API (REST JSON)

**Status: VERIFIED WORKING**

- **URL:** `https://gis.dola.colorado.gov/lookups/profile`
- **Format:** JSON REST API (no authentication required)
- **Coverage:** All 64 Colorado counties
- **Key Fields:** `countyfips`, `year`, `censusbuildingpermits`, `totalpopulation`, `householdpopulation`, `totalhousingunits`, `vacanthousingunits`, `vacancyrate`, `households`, `householdsize`, `births`, `deaths`, `netmigration`
- **Update Frequency:** Annually (current data through 2024)
- **Why it matters:** County-level building permits + demographic context in a single API call. Net migration and vacancy rates add analytical depth for lead scoring.

**Sample curl:**
```bash
# Single county (FIPS 1 = Adams)
curl -s "https://gis.dola.colorado.gov/lookups/profile?county=1&year=2024"

# All Front Range counties (loop)
for fips in 1 5 13 14 31 35 41 59 69 101 123; do
  curl -s "https://gis.dola.colorado.gov/lookups/profile?county=${fips}&year=2024"
done
```

**Front Range County FIPS Reference:**
| FIPS | County | 2024 Building Permits | 2024 Population |
|---|---|---|---|
| 1 | Adams | 2,371 | 543,760 |
| 5 | Arapahoe | 3,856 | 666,557 |
| 13 | Boulder | 1,680 | 329,996 |
| 14 | Broomfield | 405 | 78,453 |
| 31 | Denver | 3,994 | 728,309 |
| 35 | Douglas | 3,131 | 394,030 |
| 41 | El Paso | 3,849 | 752,892 |
| 59 | Jefferson | 1,172 | 578,437 |
| 69 | Larimer | 1,786 | 374,387 |
| 101 | Pueblo | 269 | 169,916 |
| 123 | Weld | 3,468 | 369,880 |

---

## 9. Colorado DWR Well Permits REST API (JSON)

**Status: VERIFIED WORKING**

- **URL:** `https://dwr.state.co.us/Rest/GET/api/v2/wellpermits/wellpermit/`
- **Documentation:** https://dwr.state.co.us/Rest/GET/Help/WellPermitGenerator
- **Format:** JSON REST API
- **Coverage:** All Colorado counties, all water divisions
- **Key Fields:** `permit`, `receipt`, `permitCurrentStatusDescr`, `county`, `associatedUses` (Domestic/Irrigation/Commercial), `permitCategoryDescr` (Residential/General Purpose), `physicalAddress`, `physicalCity`, `latitude`, `longitude`, `datePermitIssued`, `dateApplicationReceived`, `contactName`, `parcelName`, `depthTotal`, `associatedAquifers`
- **Filter Parameters:** `county`, `division`, `waterDistrict`, `designatedBasinName`, `managementDistrictName`, `modified` (date filter for incremental pulls)
- **Why it matters:** Well permits for domestic use are a LEADING indicator for rural residential development, especially in Weld, Douglas, and El Paso counties where subdivisions often precede municipal water hookups.

**Sample curl:**
```bash
# Recent well permits in Weld County
curl -s "https://dwr.state.co.us/Rest/GET/api/v2/wellpermits/wellpermit/?format=json&county=WELD&modified=01/01/2025&pageSize=25"

# Adams County residential permits
curl -s "https://dwr.state.co.us/Rest/GET/api/v2/wellpermits/wellpermit/?format=json&county=ADAMS&permitCurrentStatusDescr=Active&pageSize=25"
```

---

## 10. HUD Residential Construction Permits by County (ArcGIS Feature Service)

**Status: VERIFIED WORKING**

- **URL:** `https://services3.arcgis.com/nV0HyP5uKL48nAKr/arcgis/rest/services/Residential_Construction_Permits_by_County_CSV/FeatureServer/0`
- **Hub Page:** https://hudgis-hud.opendata.arcgis.com/datasets/HUD::residential-construction-permits-by-county/about
- **Format:** ArcGIS REST API (JSON)
- **Coverage:** All US counties (filter to Colorado)
- **Key Fields:** `NAME` (county), `STATE_NAME`, `STUSAB`, `ALL_PERMITS_2021`, `SINGLE_FAMILY_PERMITS_2021`, `ALL_MULTIFAMILY_PERMITS_2021`, `MULTIFAMILY_PERMITS_2_UNITS`, `MULTIFAMILY_PERMITS_3_4_UNIT`, `MULTIFAMILY_PERMITS_5_OR_MOR`, `GEOID`
- **Update Frequency:** Annual (latest: 2021 data)
- **Why it matters:** Pre-aggregated county-level permit data with single-family vs multifamily breakdowns. Good for historical baselines and cross-county comparison.

**Sample curl:**
```bash
curl -s "https://services3.arcgis.com/nV0HyP5uKL48nAKr/arcgis/rest/services/Residential_Construction_Permits_by_County_CSV/FeatureServer/0/query?where=STATE_NAME='Colorado'&outFields=NAME,ALL_PERMITS_2021,SINGLE_FAMILY_PERMITS_2021,ALL_MULTIFAMILY_PERMITS_2021&f=json&orderByFields=ALL_PERMITS_2021+DESC"
```

---

## 11. Legistar Web API -- Denver & Colorado Springs (REST JSON)

**Status: VERIFIED WORKING**

- **Base URL:** `https://webapi.legistar.com/v1/{client}/`
- **Format:** OData REST API (JSON)
- **No authentication required**
- **Supported Clients:** `denver`, `coloradosprings`

### Denver Planning-Related Bodies:
| Body ID | Name |
|---|---|
| 233 | Land Use, Transportation & Infrastructure Committee |
| 237 | Safety, Housing, Education & Homelessness Committee |
| 180 | Business Development Committee |

### Colorado Springs Planning-Related Bodies:
| Body ID | Name |
|---|---|
| 185 | City Planning Commission |
| 192 | City Planning Commission Work Session |

- **Key Endpoints:** `/Events` (meetings), `/Bodies` (committees), `/Matters` (legislation/ordinances), `/EventItems` (agenda items)
- **Why it matters:** Programmatic access to rezoning ordinances, land use committee agendas, and housing policy decisions. The old RSS feeds are dead; this OData API is the replacement. Filter `Matters` for rezoning ordinances as leading indicators.

**Sample curl:**
```bash
# Denver: Recent land use committee meetings
curl -s "https://webapi.legistar.com/v1/denver/Events?\$filter=EventBodyId+eq+233&\$top=10&\$orderby=EventDate+desc"

# Denver: Recent legislation (all types)
curl -s "https://webapi.legistar.com/v1/denver/Matters?\$top=10&\$orderby=MatterIntroDate+desc"

# Colorado Springs: Planning Commission meetings
curl -s "https://webapi.legistar.com/v1/coloradosprings/Events?\$filter=EventBodyId+eq+185&\$top=10&\$orderby=EventDate+desc"
```

---

## 12. data.colorado.gov SODA API -- Building Permit Counts (Socrata)

**Status: VERIFIED WORKING** (already in sources.md but now fully verified with sample data)

- **URL:** `https://data.colorado.gov/resource/v4as-sthd.json`
- **Format:** Socrata SODA API (JSON, CSV, GeoJSON)
- **Coverage:** Statewide by county and municipality
- **Key Fields:** `countyfips`, `placefips`, `area`, `year`, `cbbuildingpermit` (Census Bureau count), `sdobuildingpermit` (SDO count), `totalpopulation`, `householdpopulation`, `totalhousingunits`
- **Update Frequency:** Annual
- **Why it matters:** Direct comparison of Census Bureau vs SDO permit counts at the municipal level, paired with population context.

**Sample curl:**
```bash
# All Front Range municipalities, most recent year
curl -s "https://data.colorado.gov/resource/v4as-sthd.json?\$where=year='2022'&\$order=cbbuildingpermit+DESC&\$limit=20"
```

---

## 13. BizWest Real Estate & Construction RSS Feed

**Status: VERIFIED WORKING**

- **URL:** `https://bizwest.com/category/real-estate-construction/feed/`
- **Format:** RSS 2.0 (XML)
- **Update Frequency:** Daily (10 items in feed)
- **Coverage:** Northern Colorado / Boulder Valley (Fort Collins, Loveland, Greeley, Longmont, Boulder)
- **Why it matters:** Early announcements of annexations, development proposals, and project approvals. Recent headline (2026-03-05): "Hudson delays Bandimere annexations after letter from nearby egg farm" -- exactly the type of signal we need.

**Sample curl:**
```bash
curl -s "https://bizwest.com/category/real-estate-construction/feed/"
```

---

## 14. Denver Post Real Estate RSS Feeds

**Status: VERIFIED WORKING**

Three working feed URLs with current 2026 content:

| Feed | URL | Items |
|---|---|---|
| Colorado Real Estate Section | `https://www.denverpost.com/business/colorado-real-estate/feed/` | 10 |
| Housing Market Tag | `https://www.denverpost.com/tag/housing-market/feed/` | 10 |
| Real Estate Tag | `https://www.denverpost.com/tag/real-estate/feed/` | 10 |

- **Format:** RSS 2.0 (XML)
- **Update Frequency:** Daily
- **Coverage:** Metro Denver, Colorado Front Range
- **Why it matters:** Major development project announcements, market trend coverage, and zoning/policy changes. Recent headline (2026-03-05): "Duplexes eyed for Shops at Northfield site where apartments were proposed."

**Sample curl:**
```bash
curl -s "https://www.denverpost.com/business/colorado-real-estate/feed/"
```

---

## 15. ENR (Engineering News-Record) RSS Feeds

**Status: VERIFIED WORKING**

- **General Articles Feed:** `https://www.enr.com/rss/articles` (30 items, working)
- **Mountain States Regional Feed:** `https://www.enr.com/rss/5` (exists but currently 0 items)
- **Format:** RSS 2.0 (XML)
- **Coverage:** National (general) / CO, ID, MT, UT, WY (Mountain States)
- **Why it matters:** Large-scale construction project announcements, contractor activity, and infrastructure investment trends.

**Sample curl:**
```bash
# General ENR feed (includes Mountain States content)
curl -s "https://www.enr.com/rss/articles"
```

---

## 16. Fort Collins New Construction Permits (Socrata -- Historical)

**Status: VERIFIED WORKING** (but limited to 2000-2016 data)

- **URL:** `https://opendata.fcgov.com/resource/4nr5-i9u8.json`
- **Format:** Socrata SODA API
- **Coverage:** City of Fort Collins, 2000-2016
- **Why it matters:** Historical baseline for Fort Collins new construction trends. Use the ArcGIS endpoint (#5 above) for current data.

---

## Implementation Priority (New Sources Only)

### Immediate (this sprint -- REST APIs, no scraping)

1. **Denver Residential Construction Permits** (#1) -- ArcGIS query, 77K records, geocoded, permit-level
2. **Denver Zone Map Amendments** (#2) -- Leading indicator, polygon geometries, status tracking
3. **FRED Building Permits** (#7) -- CSV download, 6 MSA-level series, no auth
4. **DOLA Demography API** (#8) -- JSON API, all counties, permits + demographics
5. **Legistar Web API** (#11) -- OData, Denver + Colorado Springs planning agendas

### Next sprint (more ArcGIS queries)

6. **Fort Collins Building Permits** (#5) -- Both ArcGIS and Socrata working
7. **Aurora Building Permits + Dev Applications** (#6) -- MapServer, 10+ layers
8. **Denver Demolition Permits** (#3) -- Precursor signal for redevelopment
9. **DWR Well Permits** (#9) -- REST API, rural development indicator
10. **HUD County Permits** (#10) -- Historical baselines

### Ongoing (RSS monitoring)

11. **BizWest RSS** (#13) -- Northern CO development news
12. **Denver Post RSS** (#14) -- Metro Denver market signals
13. **ENR Articles RSS** (#15) -- Construction industry trends

---

## Sources Not Previously in Registry

The following sources are entirely NEW discoveries not found in the original `sources.md`:

1. Denver Residential Construction Permits (ArcGIS) -- individual permit records with valuations
2. Denver Zone Map Amendments (ArcGIS) -- rezoning as leading indicator
3. Denver Demolition Permits (ArcGIS) -- teardown-to-rebuild signal
4. Denver full service catalog (20+ additional layers: zoning, land use, affordable housing, etc.)
5. Fort Collins Socrata endpoint (SODA API in addition to ArcGIS)
6. Aurora MapServer with 10 relevant layers including Active Development Applications
7. FRED building permits CSV (6 Colorado-specific time series, no API key)
8. DOLA Demography Office REST API (building permits + demographics by county)
9. DWR Well Permits REST API (previously listed as "search form" -- now confirmed JSON API)
10. HUD residential permits by county (ArcGIS Feature Service)
11. Legistar Web API (previously listed as "iCal export, no RSS" -- now confirmed OData REST API)
12. Denver Post real estate RSS feeds (3 working feeds)
13. ENR articles RSS feed
