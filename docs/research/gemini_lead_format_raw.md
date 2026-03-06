Loaded cached credentials.
I will begin by researching the specific data requirements and industry standards for residential development leads, builder partnerships, and real estate CRM integrations to ensure the report is grounded in current market expectations.
I will now perform a targeted search to identify the exhaustive list of data fields required for development and partnership leads, specifically focusing on permit details and developer firmographics. Following this, I will research the pricing models and data coverage of key competitors like BuildZoom and Dodge Construction to provide a comprehensive competitive analysis.
I will conduct a final search for industry-standard CRM field mapping for construction and real estate leads to provide specific guidance on how to integrate permit and project data into platforms like Salesforce and HubSpot. Following this, I will synthesize all gathered information into the structured markdown document.
This research report details the requirements for actionable development leads in the residential construction industry, specifically for the "landscraper" SaaS product.

# Research Report: Real Estate Development Lead Requirements

## 1. Required Fields for a Development Lead
To be actionable, a development lead must provide both "intent" (what is happening) and "reachability" (who is doing it). The industry standard follows the **Building and Land Development Specification (BLDS)**.

### **Administrative & Identity**
- **Permit Number / ID:** Unique jurisdiction identifier.
- **Permit Type & Subtype:** (e.g., Building > New Construction, Demolition > Residential).
- **Current Status:** (Applied, Issued, Finaled, Expired).
- **Jurisdiction:** The specific City/County authority.

### **Location & Property Details**
- **Full Site Address:** Street, City, State, Zip.
- **Assessor’s Parcel Number (APN):** Critical for linking to property tax and title records.
- **Zoning District:** (e.g., R-1, C-2) to determine land-use rights.
- **Geospatial Coordinates:** Latitude/Longitude for GIS mapping.
- **Property Type:** (Single-Family, Multi-Family, Mixed-Use).

### **Project Scope**
- **Description of Work:** Raw text detailing the project (e.g., "Construct 20-unit apartment complex").
- **Valuation:** Estimated construction cost (used for tiering leads).
- **Square Footage:** Total area of the new development.
- **Unit Count:** Number of residential units being created.
- **Stories:** Vertical scale of the building.

### **Stakeholder Contact Info**
- **Property Owner:** Name/LLC, Mailing Address, Phone, Email.
- **Applicant:** Often a permit expeditor or architect.
- **Contractor of Record:** Company name, License Number, Primary Contact.
- **Architect/Engineer:** Firm name and professional license info.

---

## 2. Required Fields for a Builder/Developer Partnership Lead
When the goal is a B2B partnership, the lead must focus on the firm's capacity and reliability.

### **Company Profile**
- **Legal Entity Name & Structure:** (e.g., LLC, Joint Venture).
- **Key Decision Makers:** Principal, Director of Acquisitions, CFO (with LinkedIn profiles).
- **Geographic Footprint:** States or regions where they are active.

### **Pipeline & Experience**
- **Active Projects:** Count of projects in Pre-dev vs. Construction.
- **Pipeline Value:** Total estimated value of all active developments.
- **Historical Track Record:** Total units/sq ft delivered in the last 5–10 years.
- **Asset Specialization:** (e.g., 80% Luxury Single-Family, 20% Affordable Housing).

### **Financial & Operational Health**
- **Bonding Capacity:** Single project and aggregate limits.
- **Preferred Partnership Model:** (Fee Developer, JV Partner, Design-Build).
- **Investment Metrics:** Historical Average IRR and Equity Multiples.
- **Tech Stack:** Software used (Procore, Autodesk, BIM).

---

## 3. Lead Scoring Criteria
Industry-standard models use a **Fit vs. Intent** matrix to prioritize leads.

| Category | Criteria | High-Value Signal |
| :--- | :--- | :--- |
| **Fit (Firmographics)** | **Entity Type** | Institutional Investors, REITs, or established LLCs. |
| | **Authority** | Principal or Director-level contact. |
| | **Location** | Project is within a high-demand or recently re-zoned "hotspot." |
| **Intent (Signals)** | **Project Scale** | High valuation (>$1M) or high unit count. |
| | **Distress Signals** | Probate, tax liens, or recent "tired landlord" signals. |
| | **Timeline** | "Issued" status (immediate work) vs. "Applied" (early-stage). |
| **Frameworks** | **BANT** | Budget, Authority, Need, Timeline. |
| | **LPMAMA** | Location, Price, Motivation, Agency, Mortgage, Appointment. |

---

## 4. Common CRM Systems
Real estate firms prioritize "Speed to Lead," making API-driven integration essential.

| CRM System | Market Position | API Availability | Mapping Strategy |
| :--- | :--- | :--- | :--- |
| **Salesforce** | Enterprise Leader (~25%) | Extensive (REST/SOAP) | Use a **Custom Object** (`Permit__c`) linked to `Account`. |
| **HubSpot** | Mid-Market / Marketing | Highly Accessible REST | Use **Custom Objects** (Enterprise) or Custom Properties. |
| **Follow Up Boss** | High-Volume Teams | Simple REST / Webhooks | Use **Custom Fields** on the Lead or Deal profile. |
| **kvCORE** | Large Brokerages | Restricted REST (v2) | Map to "Notes" or specific "Lead Source" tags. |
| **Lofty (Chime)** | Tech-Forward Teams | Open REST (OAuth 2.0) | Direct mapping to Lead/Project custom fields. |
| **BoomTown** | Enterprise Lead Gen | Limited (via Partners) | Primarily integrated via Zapier or API Nation. |

---

## 5. Typical Lead Workflow
The path from receiving a lead to closing a deal typically follows a 7-phase lifecycle:

1.  **Ingestion & Scoring:** Lead is received via API/Webhook, scored based on Fit/Intent, and assigned.
2.  **Initial Outreach:** "Speed to Lead" (target <5 mins) via automated SMS or personal call.
3.  **Feasibility/Discovery:** Agent/Developer validates zoning, site constraints, and owner motivation.
4.  **Due Diligence:** Site control via option contract; environmental and soil testing.
5.  **Entitlements & Permitting:** Navigating local government for project approvals.
6.  **Construction/Procurement:** Bidding the project out to GCs or specialized trades.
7.  **Marketing & Exit:** Pre-leasing or pre-selling units before project completion.

---

## 6. Delivery Format Preferences
Users value speed and structure over "digestibility."

1.  **API / Webhook (Highest Preference):** Real-time JSON data pushed directly into CRMs. Essential for high-volume firms.
2.  **Mobile Push/SMS (High):** Immediate alerts for agents in the field; includes "Click-to-Call" the owner/developer.
3.  **Dashboard (Medium):** Real-time UI for filtering leads by geography, valuation, or permit status.
4.  **Email Digest (Low):** Useful for executive summaries (weekly) but too slow for actionable daily leads.

---

## 7. Competitive Analysis

| Competitor | Pricing Model | Data Coverage | Strengths | Gaps for Landscraper |
| :--- | :--- | :--- | :--- | :--- |
| **BuildZoom** | 2.5% Referral Fee | 350M+ Permits | Pay-on-success; vetted contractor history. | High commission cost; high competition. |
| **Dodge Network** | $6k – $12k+/yr | 750k+ Projects | Early-stage planning intel (pre-permit). | Expensive; geared toward enterprise. |
| **Construction Monitor** | $1.5k – $3k/yr | 1,900+ Jurisdictions | Established permit specialist; weekly lists. | Older UI; lacks contact enrichment. |
| **PermitData (PermitPeak)** | Subscription | County-based | **Contact Enrichment** (verified email/phone). | Limited geographic scale compared to Dodge. |

**Landscraper's Opportunity:** Bridge the gap by offering **Dodge-level early intelligence** with **PermitPeak-level contact enrichment** at a **SaaS price point** accessible to mid-market homebuilders.
