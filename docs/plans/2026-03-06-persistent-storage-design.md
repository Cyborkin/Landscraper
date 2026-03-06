# Persistent Storage Design

**Date:** 2026-03-06
**Status:** Approved

## Problem
Leads are stored in `_leads_store: list[dict]` in memory. They vanish on container restart.

## Solution
Wire the existing SQLAlchemy models (Development, Lead, Tenant) to PostgreSQL via async CRUD functions. The pipeline's delivery_node writes to DB; API endpoints query from DB.

## Key Decisions
- **Upsert key**: Add `content_hash` column to developments table. Generated from normalized fields. Allows ON CONFLICT dedup.
- **Schema relaxation**: Make jurisdiction, address_city, county, permit_type, permit_status, property_type nullable (scraped data often lacks these).
- **Tenant persistence**: POC tenant must be in DB (Lead FK requires it). Use ensure-exists pattern at startup.
- **New columns**: score_breakdown (JSONB), validation_status (VARCHAR), content_hash (VARCHAR unique) on developments.
- **Scope**: Only persist validated leads + developments. Raw collections, cycles, agent runs stay as-is.

## Data Flow
```
Pipeline dict → crud.upsert_development(session, dev_dict) → developments row
                crud.create_lead(session, development_id, tenant_id) → leads row
API GET /leads → crud.list_leads(session, filters) → joined Development+Lead → LeadOut
```
