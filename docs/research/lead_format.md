# Landscraper: Lead Format Specification

> **Version:** 0.1.0-draft
> **Date:** 2026-03-05
> **Status:** POC specification -- subject to revision after pilot integrations
> **Source:** Synthesized from Gemini research (`gemini_lead_format_raw.md`), BLDS standards, and CRM vendor documentation.

---

## Development Lead Record

Every development lead represents a single residential project (permit, zoning application, or planning-stage filing) discovered by Landscraper's ingestion pipeline.

| # | Field | Type | Required | Constraints | Description | Example |
|---|-------|------|----------|-------------|-------------|---------|
| 1 | `lead_id` | `str (UUID4)` | Yes | Unique, system-generated | Internal Landscraper identifier | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` |
| 2 | `confidence_score` | `float` | Yes | 0.0 -- 1.0 | Consensus layer output: probability that this lead represents a genuine, actionable new development | `0.87` |
| 3 | `source_count` | `int` | Yes | >= 1 | Number of independent data sources that confirmed this lead | `3` |
| 4 | `sources` | `list[str]` | Yes | Non-empty | Names of data sources that contributed to this lead | `["jefferson_county_permits", "planning_commission_agenda", "zillow_listings"]` |
| 5 | `lead_score` | `int` | Yes | 0 -- 100 | Composite score from the Lead Scoring Model (see below) | `78` |
| 6 | `permit_number` | `str` | No | Jurisdiction-specific format | Official permit or filing number from the issuing authority | `"BLD-2026-00451"` |
| 7 | `permit_type` | `str` | Yes | Enum: `new_construction`, `addition`, `demolition_rebuild`, `change_of_use`, `subdivision`, `planned_unit_development`, `rezoning` | Category of development activity | `"new_construction"` |
| 8 | `permit_status` | `str` | Yes | Enum: `pre_application`, `applied`, `under_review`, `approved`, `issued`, `in_progress`, `final`, `expired`, `denied` | Current status in the permitting lifecycle | `"applied"` |
| 9 | `jurisdiction` | `str` | Yes | -- | Issuing city, county, or special district | `"City of Thornton, CO"` |
| 10 | `address_street` | `str` | No | -- | Street address of the project site | `"1450 E 128th Ave"` |
| 11 | `address_city` | `str` | Yes | -- | City | `"Thornton"` |
| 12 | `address_state` | `str` | Yes | 2-letter USPS code | State | `"CO"` |
| 13 | `address_zip` | `str` | No | 5 or 9 digit | ZIP code | `"80241"` |
| 14 | `county` | `str` | Yes | -- | County name | `"Adams"` |
| 15 | `apn` | `str` | No | Assessor format | Assessor's Parcel Number for title/tax linkage | `"0150531200010"` |
| 16 | `latitude` | `float` | No | -90.0 -- 90.0 | WGS84 latitude | `39.9169` |
| 17 | `longitude` | `float` | No | -180.0 -- 180.0 | WGS84 longitude | `-104.9544` |
| 18 | `zoning_current` | `str` | No | -- | Current zoning designation | `"R-3"` |
| 19 | `zoning_proposed` | `str` | No | -- | Proposed zoning if a rezoning is in play | `"PUD"` |
| 20 | `property_type` | `str` | Yes | Enum: `single_family`, `townhome`, `multifamily`, `mixed_use`, `active_adult`, `manufactured` | Type of residential product | `"multifamily"` |
| 21 | `project_name` | `str` | No | -- | Marketing or filing name of the development | `"Harvest Ridge at Thornton"` |
| 22 | `description` | `str` | No | Max 2000 chars | Raw description of work from the filing | `"Construct 120-unit apartment complex with clubhouse and pool"` |
| 23 | `valuation_usd` | `float` | No | >= 0 | Estimated construction cost as declared on the filing | `18500000.00` |
| 24 | `unit_count` | `int` | No | >= 1 | Number of residential units | `120` |
| 25 | `total_sqft` | `int` | No | >= 1 | Total building square footage | `145000` |
| 26 | `lot_size_acres` | `float` | No | > 0 | Site acreage | `8.5` |
| 27 | `stories` | `int` | No | >= 1 | Number of stories | `4` |
| 28 | `owner_name` | `str` | No | -- | Property owner (person or entity) | `"Front Range Dev Partners LLC"` |
| 29 | `owner_entity_type` | `str` | No | Enum: `individual`, `llc`, `corporation`, `trust`, `reit`, `government`, `unknown` | Legal structure of the owner | `"llc"` |
| 30 | `owner_phone` | `str` | No | E.164 format | Owner phone number | `"+13035551234"` |
| 31 | `owner_email` | `str` | No | RFC 5322 | Owner email | `"jdoe@frontrangedev.com"` |
| 32 | `owner_mailing_address` | `str` | No | -- | Mailing address (may differ from site) | `"PO Box 9100, Denver, CO 80209"` |
| 33 | `applicant_name` | `str` | No | -- | Person or firm who filed the application | `"Summit Permit Services"` |
| 34 | `applicant_phone` | `str` | No | E.164 format | Applicant phone | `"+17205559876"` |
| 35 | `applicant_email` | `str` | No | RFC 5322 | Applicant email | `"permits@summitps.com"` |
| 36 | `contractor_name` | `str` | No | -- | General contractor of record | `"Hensel Phelps"` |
| 37 | `contractor_license` | `str` | No | -- | State or local license number | `"CON-2024-88431"` |
| 38 | `architect_name` | `str` | No | -- | Architect or engineer of record | `"OZ Architecture"` |
| 39 | `filing_date` | `datetime` | No | ISO 8601 | Date the permit or application was filed | `"2026-02-15T00:00:00Z"` |
| 40 | `approval_date` | `datetime` | No | ISO 8601 | Date approved (if applicable) | `null` |
| 41 | `estimated_start_date` | `datetime` | No | ISO 8601 | Projected construction start | `"2026-06-01T00:00:00Z"` |
| 42 | `estimated_completion_date` | `datetime` | No | ISO 8601 | Projected completion | `"2027-12-01T00:00:00Z"` |
| 43 | `discovered_at` | `datetime` | Yes | ISO 8601, auto-set | Timestamp when Landscraper first ingested this lead | `"2026-03-04T14:32:11Z"` |
| 44 | `updated_at` | `datetime` | Yes | ISO 8601, auto-set | Timestamp of last data refresh | `"2026-03-05T09:00:00Z"` |
| 45 | `tags` | `list[str]` | No | -- | User- or system-applied labels | `["high_value", "front_range_north", "multifamily"]` |

---

## Builder/Developer Partnership Lead Record

A partnership lead represents a company (builder, developer, or investor) that may be a strategic partner, customer, or acquisition target for a real estate firm.

| # | Field | Type | Required | Constraints | Description | Example |
|---|-------|------|----------|-------------|-------------|---------|
| 1 | `partner_id` | `str (UUID4)` | Yes | Unique, system-generated | Internal identifier | `"b2c3d4e5-f6a7-8901-bcde-f12345678901"` |
| 2 | `company_name` | `str` | Yes | -- | Legal entity name | `"Oakwood Homes LLC"` |
| 3 | `entity_type` | `str` | Yes | Enum: `llc`, `corporation`, `s_corp`, `joint_venture`, `reit`, `sole_proprietor`, `partnership`, `unknown` | Legal structure | `"llc"` |
| 4 | `headquarters_city` | `str` | No | -- | HQ city | `"Denver"` |
| 5 | `headquarters_state` | `str` | No | 2-letter USPS | HQ state | `"CO"` |
| 6 | `geographic_regions` | `list[str]` | No | -- | Regions where the firm is active | `["Front Range", "Colorado Springs", "Northern Colorado"]` |
| 7 | `website` | `str` | No | Valid URL | Company website | `"https://oakwoodhomes.com"` |
| 8 | `primary_contact_name` | `str` | No | -- | Key decision-maker | `"Maria Torres"` |
| 9 | `primary_contact_title` | `str` | No | -- | Title / role | `"VP of Land Acquisition"` |
| 10 | `primary_contact_email` | `str` | No | RFC 5322 | Email | `"mtorres@oakwoodhomes.com"` |
| 11 | `primary_contact_phone` | `str` | No | E.164 | Phone | `"+13035557890"` |
| 12 | `primary_contact_linkedin` | `str` | No | Valid URL | LinkedIn profile URL | `"https://linkedin.com/in/mariatorres"` |
| 13 | `active_project_count` | `int` | No | >= 0 | Number of projects currently in pre-dev or construction | `12` |
| 14 | `pipeline_value_usd` | `float` | No | >= 0 | Total estimated value of active pipeline | `85000000.00` |
| 15 | `historical_units_delivered` | `int` | No | >= 0 | Total units delivered in last 10 years | `2400` |
| 16 | `historical_sqft_delivered` | `int` | No | >= 0 | Total square footage delivered | `3600000` |
| 17 | `asset_specialization` | `dict[str, float]` | No | Values sum to 1.0 | Breakdown of product focus | `{"single_family": 0.6, "townhome": 0.25, "multifamily": 0.15}` |
| 18 | `preferred_partnership_model` | `str` | No | Enum: `fee_developer`, `jv_partner`, `design_build`, `turnkey`, `unknown` | How the firm prefers to structure deals | `"jv_partner"` |
| 19 | `bonding_capacity_single_usd` | `float` | No | >= 0 | Single-project bonding limit | `25000000.00` |
| 20 | `bonding_capacity_aggregate_usd` | `float` | No | >= 0 | Aggregate bonding limit | `75000000.00` |
| 21 | `confidence_score` | `float` | Yes | 0.0 -- 1.0 | Consensus layer output for data quality/completeness | `0.72` |
| 22 | `source_count` | `int` | Yes | >= 1 | Number of sources that contributed data | `2` |
| 23 | `sources` | `list[str]` | Yes | Non-empty | Source names | `["colorado_sos", "linkedin_enrichment"]` |
| 24 | `discovered_at` | `datetime` | Yes | ISO 8601 | First ingestion timestamp | `"2026-03-01T10:15:00Z"` |
| 25 | `updated_at` | `datetime` | Yes | ISO 8601 | Last data refresh | `"2026-03-05T09:00:00Z"` |

---

## Lead Scoring Model

Composite score range: **0 -- 100**. All weights sum to exactly 100.

The model blends two dimensions: **Fit** (is this project the right profile?) and **Intent** (how likely and imminent is real construction activity?). A third dimension, **Data Quality**, ensures we only surface leads we can stand behind.

| # | Factor | Dimension | Weight | Scoring Criteria |
|---|--------|-----------|--------|------------------|
| 1 | **Project Scale** | Intent | **20** | `valuation_usd >= $5M` = 20 pts; `$1M--$5M` = 14 pts; `$500K--$1M` = 8 pts; `< $500K` = 3 pts; unknown = 5 pts |
| 2 | **Permit Status / Timeline** | Intent | **15** | `issued` or `in_progress` = 15 pts; `approved` = 12 pts; `under_review` = 9 pts; `applied` = 6 pts; `pre_application` = 3 pts |
| 3 | **Unit Count** | Intent | **10** | `>= 50 units` = 10 pts; `20--49` = 7 pts; `5--19` = 4 pts; `< 5` = 2 pts; unknown = 3 pts |
| 4 | **Property Type Fit** | Fit | **10** | `multifamily` or `mixed_use` = 10 pts; `townhome` = 7 pts; `single_family` (subdivision) = 5 pts; `manufactured` = 3 pts |
| 5 | **Location Demand** | Fit | **10** | High-growth corridor (e.g., I-25 North, US-36) = 10 pts; moderate growth = 6 pts; stable/rural = 3 pts |
| 6 | **Owner Entity Type** | Fit | **8** | `reit` or `corporation` = 8 pts; `llc` = 6 pts; `trust` = 4 pts; `individual` = 2 pts; `unknown` = 1 pt |
| 7 | **Contact Completeness** | Data Quality | **10** | Owner phone + email + name = 10 pts; 2 of 3 = 7 pts; 1 of 3 = 3 pts; none = 0 pts |
| 8 | **Recency** | Intent | **7** | Filed within 7 days = 7 pts; 8--30 days = 5 pts; 31--90 days = 3 pts; > 90 days = 1 pt |
| 9 | **Confidence Score** | Data Quality | **5** | `>= 0.9` = 5 pts; `0.7--0.89` = 4 pts; `0.5--0.69` = 2 pts; `< 0.5` = 0 pts |
| 10 | **Source Corroboration** | Data Quality | **5** | `source_count >= 3` = 5 pts; `2` = 3 pts; `1` = 1 pt |
| | | | **100** | |

**Score tiers:**
- **Hot (80--100):** Immediate outreach recommended. High value, strong signals, verified contacts.
- **Warm (50--79):** Worth pursuing. May need enrichment on contacts or project details.
- **Monitor (20--49):** Early-stage or incomplete. Queue for re-scoring on next data refresh.
- **Cold (0--19):** Low fit or stale. Archive after 90 days without score change.

---

## CRM Integration Targets (POC)

For the proof-of-concept, we target **Salesforce** and **HubSpot** -- the two platforms with the most accessible APIs and the widest adoption among our target customer segment.

### Salesforce

**Strategy:** Create a custom object `Development_Lead__c` linked to the standard `Account` object. This avoids polluting the standard Lead/Opportunity pipeline and allows real estate firms to keep their existing sales process intact.

| Landscraper Field | Salesforce Object | Salesforce Field | SF Type | Notes |
|-------------------|-------------------|------------------|---------|-------|
| `lead_id` | `Development_Lead__c` | `Landscraper_ID__c` | `Text(36)` | External ID, upsert key |
| `confidence_score` | `Development_Lead__c` | `Confidence_Score__c` | `Percent` | Displayed as percentage |
| `lead_score` | `Development_Lead__c` | `Lead_Score__c` | `Number(3,0)` | 0--100 |
| `permit_number` | `Development_Lead__c` | `Permit_Number__c` | `Text(50)` | |
| `permit_type` | `Development_Lead__c` | `Permit_Type__c` | `Picklist` | Values match our enum |
| `permit_status` | `Development_Lead__c` | `Permit_Status__c` | `Picklist` | |
| `address_street` | `Development_Lead__c` | `Site_Street__c` | `Text(255)` | |
| `address_city` | `Development_Lead__c` | `Site_City__c` | `Text(100)` | |
| `address_state` | `Development_Lead__c` | `Site_State__c` | `Text(2)` | |
| `address_zip` | `Development_Lead__c` | `Site_Zip__c` | `Text(10)` | |
| `valuation_usd` | `Development_Lead__c` | `Valuation__c` | `Currency(12,2)` | |
| `unit_count` | `Development_Lead__c` | `Unit_Count__c` | `Number(5,0)` | |
| `property_type` | `Development_Lead__c` | `Property_Type__c` | `Picklist` | |
| `owner_name` | `Account` | `Name` | `Text` | Lookup or create Account |
| `owner_phone` | `Account` | `Phone` | `Phone` | |
| `owner_email` | `Account` | `PersonEmail` or custom | `Email` | |
| `filing_date` | `Development_Lead__c` | `Filing_Date__c` | `Date` | |
| `discovered_at` | `Development_Lead__c` | `Discovered_At__c` | `DateTime` | |
| `source_count` | `Development_Lead__c` | `Source_Count__c` | `Number(2,0)` | |
| `sources` | `Development_Lead__c` | `Sources__c` | `LongTextArea` | JSON array stored as text |

**Auth:** OAuth 2.0 JWT Bearer flow (server-to-server, no user interaction).
**API:** REST Composite API for batched upserts (up to 25 records per request).

### HubSpot

**Strategy:** Use HubSpot Custom Objects (available on Enterprise tier) or, for POC with lower-tier accounts, map to **Deals** with custom properties and a dedicated pipeline named "Development Leads."

| Landscraper Field | HubSpot Object | HubSpot Property | HS Type | Notes |
|-------------------|----------------|-------------------|---------|-------|
| `lead_id` | Custom Object / Deal | `landscraper_id` | `string` | Unique identifier for dedup |
| `confidence_score` | Custom Object / Deal | `confidence_score` | `number` | 0--100 (HubSpot lacks native 0--1 float; multiply by 100) |
| `lead_score` | Custom Object / Deal | `lead_score` | `number` | |
| `permit_number` | Custom Object / Deal | `permit_number` | `string` | |
| `permit_type` | Custom Object / Deal | `permit_type` | `enumeration` | |
| `permit_status` | Custom Object / Deal | `permit_status` | `enumeration` | |
| `address_street` | Custom Object / Deal | `site_address` | `string` | Full address concatenated |
| `valuation_usd` | Custom Object / Deal | `valuation` | `number` | |
| `unit_count` | Custom Object / Deal | `unit_count` | `number` | |
| `property_type` | Custom Object / Deal | `property_type` | `enumeration` | |
| `owner_name` | Company | `name` | `string` | Associate to Company record |
| `owner_phone` | Company / Contact | `phone` | `string` | |
| `owner_email` | Contact | `email` | `string` | |
| `filing_date` | Custom Object / Deal | `filing_date` | `date` | |
| `discovered_at` | Custom Object / Deal | `discovered_at` | `datetime` | |
| `source_count` | Custom Object / Deal | `source_count` | `number` | |
| `sources` | Custom Object / Deal | `sources` | `string` | Semicolon-delimited list |

**Auth:** OAuth 2.0 authorization code flow or private app access tokens (simpler for POC).
**API:** HubSpot CRM API v3 -- batch create/update endpoints (up to 100 records per request).

---

## Lead Lifecycle

```
 +-------------+      +--------------+      +-----------+      +------------+      +------------+
 |  DISCOVERY  | ---> |  ENRICHMENT  | ---> |  SCORING  | ---> |  DELIVERY  | ---> |  FEEDBACK  |
 +-------------+      +--------------+      +-----------+      +------------+      +------------+
       |                     |                    |                   |                    |
   Scrape permits       Cross-ref with       Apply scoring       Push to CRM,        Track open
   Parse agendas        property/tax DB      model (100-pt)     email, Slack        rates, agent
   Monitor zoning       Enrich contacts      Assign tier                             actions, and
   Ingest RSS/APIs      via clearbit/        (Hot/Warm/                              deal outcomes
                        apollo/manual        Monitor/Cold)                           to refine
                        Geocode addresses                                            scoring model
```

### Phase Details

| Phase | Trigger | Key Actions | Output | SLA Target |
|-------|---------|-------------|--------|------------|
| **Discovery** | Scheduled scrape (cron) or webhook from jurisdiction API | Ingest raw permit/zoning/planning data; deduplicate against existing `lead_id`s; create provisional lead record | Raw lead with `permit_type`, `permit_status`, `address_*`, `jurisdiction`, `description` | Scrape frequency: every 6 hours for active jurisdictions |
| **Enrichment** | New lead created or `updated_at` older than 7 days | Cross-reference APN against county assessor/tax records; geocode address; look up owner contact info via enrichment APIs; pull contractor/architect from permit; increment `source_count` and append to `sources` | Enriched lead with owner contacts, `apn`, `lat/lng`, `valuation_usd` | < 30 minutes after discovery |
| **Scoring** | Enrichment complete | Run the 10-factor scoring model; compute `lead_score` and assign tier; set `confidence_score` from consensus layer | Scored lead with `lead_score`, `confidence_score`, tier label | < 5 minutes after enrichment |
| **Delivery** | Score computed and tier is Hot or Warm (or matches user filter) | Push to configured channels: CRM sync, email digest, Slack webhook, API poll | Delivered payload (see Delivery Channels below); delivery receipt logged | < 15 minutes after scoring for Hot leads; daily batch for Warm/Monitor |
| **Feedback** | User action in CRM or explicit feedback via API | Record outcome: contacted, qualified, converted, rejected; capture rejection reason; feed back into scoring model weights via periodic retraining | Updated lead status; scoring model adjustment log | Continuous; model retrain monthly |

---

## Delivery Channels (POC)

### 1. Email Digest

- **Frequency:** Daily (Hot leads) and Weekly (Warm + summary)
- **Format:** HTML email with responsive table layout
- **Content:** Top 10 leads by score, each showing: project name/address, permit type/status, valuation, unit count, owner name, lead score badge (color-coded by tier)
- **Personalization:** Filtered by user's saved geographic and property-type preferences
- **Provider:** SendGrid or AWS SES via transactional email API
- **Unsubscribe:** One-click, CAN-SPAM compliant

### 2. Slack Webhook

- **Trigger:** Real-time for Hot leads (score >= 80); batched for Warm leads (hourly summary)
- **Format:** Slack Block Kit message
- **Content per lead:**
  - Header: project name + tier badge
  - Fields: address, permit status, valuation, unit count, owner name
  - Action button: "View in Landscraper" (deep link to lead detail page)
- **Configuration:** User provides a Slack Incoming Webhook URL; Landscraper POSTs to it
- **Rate limit:** Max 1 message per second per webhook (Slack limit)

### 3. API Endpoint

RESTful endpoint for programmatic consumption and CRM integration middleware.

**Endpoint:** `GET /api/v1/leads`

**Authentication:** Bearer token (API key issued per customer account)

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tier` | `str` | `null` (all) | Filter by tier: `hot`, `warm`, `monitor`, `cold` |
| `property_type` | `str` | `null` | Filter by property type enum |
| `county` | `str` | `null` | Filter by county name |
| `min_score` | `int` | `0` | Minimum lead score |
| `since` | `datetime` | `null` | Only leads discovered after this timestamp (ISO 8601) |
| `page` | `int` | `1` | Pagination page |
| `page_size` | `int` | `50` | Results per page (max 200) |

**Response JSON Payload:**

```json
{
  "meta": {
    "total_count": 142,
    "page": 1,
    "page_size": 50,
    "next_page_url": "/api/v1/leads?page=2&page_size=50&tier=hot"
  },
  "leads": [
    {
      "lead_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "confidence_score": 0.87,
      "source_count": 3,
      "sources": [
        "jefferson_county_permits",
        "planning_commission_agenda",
        "zillow_listings"
      ],
      "lead_score": 78,
      "tier": "warm",
      "permit_number": "BLD-2026-00451",
      "permit_type": "new_construction",
      "permit_status": "applied",
      "jurisdiction": "City of Thornton, CO",
      "address": {
        "street": "1450 E 128th Ave",
        "city": "Thornton",
        "state": "CO",
        "zip": "80241",
        "county": "Adams"
      },
      "coordinates": {
        "latitude": 39.9169,
        "longitude": -104.9544
      },
      "apn": "0150531200010",
      "zoning": {
        "current": "R-3",
        "proposed": "PUD"
      },
      "property_type": "multifamily",
      "project_name": "Harvest Ridge at Thornton",
      "description": "Construct 120-unit apartment complex with clubhouse and pool",
      "valuation_usd": 18500000.00,
      "unit_count": 120,
      "total_sqft": 145000,
      "lot_size_acres": 8.5,
      "stories": 4,
      "stakeholders": {
        "owner": {
          "name": "Front Range Dev Partners LLC",
          "entity_type": "llc",
          "phone": "+13035551234",
          "email": "jdoe@frontrangedev.com",
          "mailing_address": "PO Box 9100, Denver, CO 80209"
        },
        "applicant": {
          "name": "Summit Permit Services",
          "phone": "+17205559876",
          "email": "permits@summitps.com"
        },
        "contractor": {
          "name": "Hensel Phelps",
          "license": "CON-2024-88431"
        },
        "architect": {
          "name": "OZ Architecture"
        }
      },
      "dates": {
        "filing_date": "2026-02-15T00:00:00Z",
        "approval_date": null,
        "estimated_start": "2026-06-01T00:00:00Z",
        "estimated_completion": "2027-12-01T00:00:00Z"
      },
      "discovered_at": "2026-03-04T14:32:11Z",
      "updated_at": "2026-03-05T09:00:00Z",
      "tags": ["high_value", "front_range_north", "multifamily"]
    }
  ]
}
```

**Webhook variant:** `POST` to customer-configured URL with the same `leads` array payload. Includes `X-Landscraper-Signature` header (HMAC-SHA256 of the body with shared secret) for verification.

---

## Competitive Positioning

### Summary Comparison

| Capability | **Landscraper** | **Dodge / SmartMarket** | **Construction Monitor** | **PermitData (PermitPeak)** | **BuildZoom** |
|------------|:-:|:-:|:-:|:-:|:-:|
| **Early-stage intel** (pre-permit: zoning, planning agendas) | Yes | Yes | No | No | No |
| **Permit tracking** | Yes | Yes | Yes | Yes | Yes |
| **Contact enrichment** (owner phone/email) | Yes | No | No | Yes | Partial |
| **Lead scoring** | Yes (automated, 100-pt model) | No (raw data) | No | No | Implicit (reviews) |
| **CRM integration** (Salesforce, HubSpot) | Native (POC) | CSV/manual | CSV export | Webhook | No |
| **Geographic focus** | CO Front Range (expanding) | National | National (1,900 jurisdictions) | Regional (county-based) | National |
| **Pricing model** | SaaS subscription ($200--$800/mo target) | $6K--$12K+/yr | $1.5K--$3K/yr | Subscription | 2.5% referral fee |
| **Real-time delivery** | Webhook + API + Slack | Email alerts | Weekly batch | Daily email | On-demand search |
| **Multi-source consensus** | Yes (`confidence_score`, `source_count`) | Single source | Single source | Single source | Single source |

### Gap Analysis and Differentiators

**Our core differentiator** is the combination of three capabilities that no single competitor offers together:

1. **Early-stage intelligence at SaaS pricing.** Dodge/SmartMarket is the only competitor with pre-permit planning data, but their $6K--$12K/yr price point locks out mid-market homebuilders, small developers, and individual real estate teams. Landscraper targets $200--$800/mo -- an order of magnitude more accessible.

2. **Contact enrichment built in.** Construction Monitor and Dodge deliver project data but leave users to manually research who to call. PermitPeak enriches contacts but lacks early-stage signals. Landscraper combines both: early project discovery with enriched, verified stakeholder contacts.

3. **Multi-source consensus layer.** Every competitor is a single-source product. Landscraper cross-references permits, zoning filings, planning agendas, property records, and enrichment APIs, then produces a `confidence_score` that tells users how trustworthy the lead is. This reduces false positives and wasted outreach.

**Known gaps to close post-POC:**

| Gap | Impact | Mitigation Plan |
|-----|--------|-----------------|
| Geographic coverage limited to CO Front Range | Cannot serve national firms | Expand to top-10 growth MSAs in Year 1 (Phoenix, Austin, Boise, Raleigh, etc.) |
| No mobile app | Field agents prefer mobile alerts | Slack + SMS delivery covers mobile use case for POC; native app in v2 |
| No historical analytics | Cannot show market trends | Build analytics dashboard post-POC once data accumulates (6+ months) |
| Scoring model not yet validated | Weights are heuristic, not ML-trained | Feedback loop in lead lifecycle allows model retraining with real outcomes |
