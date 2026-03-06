Loaded cached credentials.
I will begin by researching building permit and assessor portals for the 10 specified Colorado Front Range counties to identify direct data sources and access methods.

I will now research USPS growth data, utility connection processes for major Front Range providers, CDOT infrastructure project portals, and Colorado water rights transfers to identify leading indicators for new construction.

I will now complete the research by investigating MLS new construction feeds, identifying key developer portals, and searching for non-obvious indicators such as soil testing permits and fiber infrastructure expansion plans.

This research report provides a comprehensive mapping of data sources for tracking residential construction activity across the 10-county Colorado Front Range corridor.

# Front Range Residential Construction Data Sources

## 1. County Building Permit & Assessor Portals
These are the most reliable "ground truth" sources for active construction. Most Front Range counties use **Accela Citizen Access** or **GovOnline**, which are scrapeable but often require handling JavaScript and paginated results.

| Source Name & URL | Data Type | Access Method | Scraping Complexity | Update Frequency | Geographic Coverage | Quality (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Denver e-Permits** [denvergov.org/epermits](https://www.denvergov.org/epermits) | Building Permits | Public Website | High (JS, Search-based) | Daily | Denver County | 5 (Official) |
| **Jeffco Citizen Portal** [planning.jeffco.us](https://planning.jeffco.us/citizenportal) | Permits/Planning | Public (Reg Req) | High (Auth, JS) | Daily | Jefferson County | 4 (Auth req) |
| **Adams E-Permit Center** [epermits.adcogov.org](https://epermits.adcogov.org/citizenaccess/) | Permits | Public Website | High (Accela JS) | Daily | Adams County | 5 (Robust) |
| **Arapahoe Accela** [aca-prod.accela.com/ARAPAHOE](https://aca-prod.accela.com/ARAPAHOE/Default.aspx) | Permits | Public Website | High (Accela JS) | Daily | Arapahoe County | 4 (Session-heavy) |
| **Boulder County Permits** [bouldercounty.org](https://www.bouldercounty.org/property-and-land/land-use/building/permit-records/) | Permits | Public Website | Moderate (Static/Search) | Daily | Unincorp. Boulder | 4 (Good UI) |
| **Douglas Building Services** [douglas.co.us/building](https://www.douglas.co.us/building-division/online-services/) | Permits | Public Website | Moderate | Daily | Douglas County | 5 (High growth) |
| **Larimer Community Dev** [onlineportal.larimer.org](https://onlineportal.larimer.org/v3/customer/login) | Permits | Public (CSS) | High (JS/Portal) | Daily | Larimer County | 4 (Modern CSS) |
| **Weld E-Permit Center** [weld.gov/epermit](https://www.weld.gov/Government/Departments/Building/E-Permit-Center) | Permits | Public Website | Moderate | Daily | Weld County | 5 (Highest growth) |
| **PPRBD (El Paso)** [pprbd.org](https://www.pprbd.org/) | Permits | Public Website | Moderate (Clean HTML) | Real-time | El Paso, Springs | 5 (Excellent API) |
| **Broomfield Citizen Access** [broomfield.org/citizenaccess](https://www.broomfield.org/263/Building) | Permits | Public Website | High (Accela JS) | Daily | Broomfield County | 4 (Combined city) |

## 2. Municipal Planning & Zoning Agendas
Agendas often list developments 6-24 months *before* permit issuance. Most use **Legistar** or **CivicClerk**, which often provide RSS feeds.

| Source Name & URL | Data Type | Access Method | Scraping Complexity | Update Frequency | Coverage | Quality (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Denver Planning Board** [denver.legistar.com](https://denver.legistar.com/Calendar.aspx) | Agendas/Minutes | RSS/Public Web | Low (RSS) | Bi-weekly | Denver | 5 (Early signal) |
| **Aurora Planning & Zoning** [aurora.legistar.com](https://aurora.legistar.com/Calendar.aspx) | Agendas/Minutes | RSS/Public Web | Low (RSS) | Bi-weekly | Aurora | 5 |
| **LakewoodSpeaks** [lakewoodspeaks.org](https://www.LakewoodSpeaks.org) | Case Details | Public Portal | Moderate (Interactive) | Weekly | Lakewood | 5 (Best detail) |
| **Fort Collins Planning** [fortcollins.legistar.com](https://fortcollins.legistar.com/Calendar.aspx) | Agendas/Minutes | RSS/Public Web | Low (RSS) | Monthly | Fort Collins | 4 |
| **Colorado Springs Planning** [coloradosprings.legistar.com](https://coloradosprings.legistar.com/Calendar.aspx) | Agendas/Minutes | RSS/Public Web | Low (RSS) | Monthly | Colo Springs | 5 |

## 3. State & Federal Data Sources
These sources provide aggregated trends and regulatory checkpoints.

| Source Name & URL | Data Type | Access Method | Scraping Complexity | Frequency | Coverage | Quality (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DORA Electrical/Plumbing** [dora.colorado.gov](https://dora.colorado.gov/professions-and-occupations/electrical-and-plumbing-permits) | Trade Permits | Public Search | High (Portal) | Daily | Statewide | 5 (Final stage) |
| **USPS PostalPro Growth** [postalpro.usps.com](https://postalpro.usps.com/address-quality/delivery-statistics) | New Addresses | Public Tool | Moderate (CASS data) | Monthly | ZIP-level | 4 (Address counts) |
| **Census Bureau BPS** [census.gov/construction/bps](https://www.census.gov/construction/bps/index.html) | Permit Survey | API / Download | Low (JSON API) | Monthly | County-level | 5 (Official stats) |
| **CDWR Water Well Permits** [dwr.state.co.us](https://dwr.state.co.us/Tools/WellPermits) | Well Permits | Public Website | Moderate (Search) | Daily | Rural Front Range | 4 (Leading ind.) |

## 4. Utility & Infrastructure Leading Indicators
Utility applications are "leading" indicators because they occur before or during the foundation stage.

| Source Name & URL | Data Type | Access Method | Scraping Complexity | Frequency | Coverage | Quality (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Denver Water Project Map** [denverwater.org/construction](https://www.denverwater.org/construction) | Main Extensions | Map / PDF | High (ArcGIS/PDF) | Weekly | Denver Metro | 4 (Physical work) |
| **CDOT OTIS** [otis.dot.state.co.us](https://otis.dot.state.co.us/) | Road/Infra | Map/Portal | High (ArcGIS) | Monthly | Front Range | 3 (Access points) |
| **Colo. Springs Utils** [csu.org/ConnectionHub](https://www.csu.org/Pages/DevelopmentRequests.aspx) | Utility Requests | Public (Reg Req) | High (Auth) | Daily | El Paso County | 4 |
| **Broadband Deployment** [broadband.colorado.gov](https://broadband.colorado.gov/) | Fiber Expansions | Map (ArcGIS) | High (GIS Service) | Quarterly | Front Range | 3 (Speculative) |

## 5. Market & Industry Intelligence
Direct builder activity and sales listings.

| Source Name & URL | Data Type | Access Method | Scraping Complexity | Frequency | Coverage | Quality (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REcolorado New Homes** [recolorado.com](https://www.recolorado.com) | MLS Listings | Public Website | Moderate (JS) | Real-time | Denver Metro | 5 (Accurate) |
| **Lennar Communities** [lennar.com/colorado](https://www.lennar.com/new-homes/colorado/denver) | Builder Map | Public Website | Moderate (Map data) | Weekly | Front Range | 4 (Speculative) |
| **BizWest Projects** [bizwest.com/real-estate](https://bizwest.com/category/real-estate-construction/) | News / Leads | Paywall / RSS | Low (RSS) | Daily | Northern CO | 4 (Contextual) |
| **SEC EDGAR (10-K/Q)** [sec.gov/edgar](https://www.sec.gov/edgar/search/) | Regional CapEx | API (JSON) | Low (REST) | Quarterly | National/Regional | 3 (High-level) |

## 6. Non-Obvious Leading Indicators

### Water Rights Transfers & Wells
*   **Source:** [Colorado Division of Water Resources (DWR)](https://dwr.state.co.us/Tools/WaterRights/Transactions)
*   **Significance:** Large developments in Weld and Larimer often require "Change of Water Right" cases in Water Court years before building.
*   **Access:** Public database search by basin (Division 1 = South Platte).

### School District Enrollment Projections
*   **Source:** [St. Vrain Valley Schools Projections](https://www.svvsd.org/departments/planning/) / [27J Schools Planning](https://www.sd27j.org/domain/56)
*   **Significance:** Districts like 27J (Brighton/Thornton) publish specific GIS maps of "Future Student Yield" from approved developments.
*   **Quality:** 5 (Very accurate for master-planned communities).

### Geotechnical & Soil Testing
*   **Source:** [Colorado Geological Survey Land Use Reviews](https://coloradogeologicalsurvey.org/land-use/)
*   **Significance:** State law requires geologic reviews for subdivisions. These reports are often the first public record of a developer's intent to build on a specific parcel.
*   **Access:** Searchable by county/municipality.

### Fiber/Telecom Expansion
*   **Source:** [Google Fiber Lakewood/Westminster](https://fiber.google.com/locations/colorado-springs/) / [Ting Colorado Springs](https://www.csu.org/Pages/Fiber.aspx)
*   **Significance:** Digging for fiber in "greenfield" areas often precedes residential permits by 6 months.

## Summary Recommendation for Scraping Strategy
1.  **High Signal/Low Effort:** Monitor **Legistar RSS feeds** for all Front Range cities to capture project names and developer identities at the planning stage.
2.  **Ground Truth:** Use a headless browser (Playwright/Selenium) to scrape **PPRBD (El Paso)** and **Adams County Accela** portals, as they represent the highest growth volume.
3.  **The "Water Gap":** In the North Front Range (Weld/Larimer), **DWR Well Permits** and **Water Court Filings** are the only way to see developments that are "off-grid" or in early pre-platting.
