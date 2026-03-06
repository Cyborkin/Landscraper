"""ArcGIS FeatureServer scraper for municipal permit data.

Queries ArcGIS REST API endpoints from Colorado Front Range cities
that publish building permits as public FeatureServer layers.
"""

from datetime import datetime, timezone
from typing import Any

import httpx

from .base import BaseScraper

# Verified ArcGIS FeatureServer endpoints for Front Range cities
ARCGIS_SOURCES = {
    "fort_collins_permits": {
        "url": (
            "https://services1.arcgis.com/dLpFH5mwVvxSN4OE/arcgis/rest/services/"
            "Building_Permits/FeatureServer/0/query"
        ),
        "where": "PERMITTYPE LIKE '%Residential%New%'",
        "fields": "PERMITNUM,PERMITTYPE,B1_WORK_DESC,ADDRESS,B1_APPL_STATUS,SUBDIVISIONNAME",
        "field_map": {
            "permit_number": "PERMITNUM",
            "permit_type": "PERMITTYPE",
            "description": "B1_WORK_DESC",
            "address_street": "ADDRESS",
            "permit_status": "B1_APPL_STATUS",
            "subdivision": "SUBDIVISIONNAME",
        },
        "city": "Fort Collins",
        "county": "Larimer",
    },
    "aurora_permits": {
        "url": (
            "https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/156/query"
        ),
        "where": "FolderType IN ('RE','RM','RN','RS')",
        "fields": "Permit_,FolderType,FolderDesc,FolderDescription,FULL_ADDRESS,valuation,IssueDate",
        "field_map": {
            "permit_number": "Permit_",
            "permit_type": "FolderDesc",
            "description": "FolderDescription",
            "address_street": "FULL_ADDRESS",
            "valuation": "valuation",
            "filing_date": "IssueDate",
        },
        "city": "Aurora",
        "county": "Arapahoe",
    },
    "denver_residential_permits": {
        "url": (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316/query"
        ),
        "where": "CLASS='New Building'",
        "fields": "PERMIT_NUM,DATE_ISSUED,DATE_RECEIVED,ADDRESS,CLASS,VALUATION,CONTRACTOR_NAME,NEIGHBORHOOD,UNITS",
        "field_map": {
            "permit_number": "PERMIT_NUM",
            "permit_type": "CLASS",
            "address_street": "ADDRESS",
            "valuation": "VALUATION",
            "filing_date": "DATE_ISSUED",
            "contractor_name": "CONTRACTOR_NAME",
            "subdivision": "NEIGHBORHOOD",
            "unit_count": "UNITS",
        },
        "default_permit_status": "issued",
        "city": "Denver",
        "county": "Denver",
    },
    "denver_rezoning": {
        "url": (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_ZONE_MAPAMENDMENTS_A/FeatureServer/356/query"
        ),
        "where": "STATUS IN ('Pending','Approved')",
        "fields": "APP_NUM,APP_DATE,STATUS,FROM_ZONE_DESC,ZONE_DESCRIPTION,ZONE_DIST_TYPE,NBHD,ACRES,HEIGHT_STORIES",
        "field_map": {
            "permit_number": "APP_NUM",
            "permit_status": "STATUS",
            "permit_type": "ZONE_DIST_TYPE",
            "description": "ZONE_DESCRIPTION",
            "subdivision": "NBHD",
            "filing_date": "APP_DATE",
        },
        "city": "Denver",
        "county": "Denver",
    },
    "denver_demolition_permits": {
        "url": (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_DEV_DEMOLITIONPERMIT_P/FeatureServer/318/query"
        ),
        "where": "1=1",
        "fields": "PERMIT_NUM,DATE_ISSUED,DATE_RECEIVED,ADDRESS,VALUATION,CONTRACTOR_NAME,NEIGHBORHOOD",
        "field_map": {
            "permit_number": "PERMIT_NUM",
            "permit_type": "DEMOLITION",
            "address_street": "ADDRESS",
            "valuation": "VALUATION",
            "filing_date": "DATE_ISSUED",
            "contractor_name": "CONTRACTOR_NAME",
            "subdivision": "NEIGHBORHOOD",
        },
        "default_permit_status": "issued",
        "default_permit_type": "Demolition",
        "city": "Denver",
        "county": "Denver",
    },
    "aurora_dev_applications": {
        "url": (
            "https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/180/query"
        ),
        "where": "FolderStatus IN ('Active','Under Review')",
        "fields": "DANum,FolderName,folderdescription,FolderStatus,Address,SiteAcreage,PropNumLots,PropNumDwell,ExistZone,PropZone",
        "field_map": {
            "permit_number": "DANum",
            "permit_type": "FolderName",
            "description": "folderdescription",
            "permit_status": "FolderStatus",
            "address_street": "Address",
            "unit_count": "PropNumDwell",
        },
        "city": "Aurora",
        "county": "Arapahoe",
    },
    "denver_commercial_permits": {
        "url": (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_DEV_COMMERCIALCONSTPERMIT_P/FeatureServer/0/query"
        ),
        "where": "CLASS='New Building'",
        "fields": "PERMIT_NUM,DATE_ISSUED,DATE_RECEIVED,ADDRESS,CLASS,VALUATION,CONTRACTOR_NAME,NEIGHBORHOOD",
        "field_map": {
            "permit_number": "PERMIT_NUM",
            "permit_type": "CLASS",
            "address_street": "ADDRESS",
            "valuation": "VALUATION",
            "filing_date": "DATE_ISSUED",
            "contractor_name": "CONTRACTOR_NAME",
            "subdivision": "NEIGHBORHOOD",
        },
        "default_permit_status": "issued",
        "city": "Denver",
        "county": "Denver",
    },
}


class ArcGISScraper(BaseScraper):
    source_type = "api"

    def __init__(self, source_key: str):
        config = ARCGIS_SOURCES.get(source_key)
        if not config:
            raise ValueError(f"Unknown ArcGIS source: {source_key}")
        self.source_name = source_key
        self.config = config

    def _get_field(self, attrs: dict, canonical: str) -> str | None:
        """Resolve a canonical field name to its source-specific value."""
        field_map = self.config.get("field_map", {})
        source_field = field_map.get(canonical)
        if source_field:
            return attrs.get(source_field)
        return None

    async def scrape(self) -> list[dict[str, Any]]:
        params = {
            "where": self.config["where"],
            "outFields": self.config["fields"],
            "outSR": 4326,
            "f": "json",
            "resultRecordCount": 200,
            "orderByFields": "OBJECTID DESC",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.config["url"], params=params)
            response.raise_for_status()

        data = response.json()
        features = data.get("features", [])
        records = []

        for feature in features:
            attrs = feature.get("attributes", {})
            geometry = feature.get("geometry", {})

            permit_num = self._get_field(attrs, "permit_number") or ""
            description = self._get_field(attrs, "description") or ""
            address = self._get_field(attrs, "address_street") or ""

            # Convert epoch ms to ISO date string
            filing_raw = self._get_field(attrs, "filing_date")
            filing_date = None
            if filing_raw and isinstance(filing_raw, (int, float)):
                filing_date = datetime.fromtimestamp(
                    filing_raw / 1000, tz=timezone.utc
                ).isoformat()
            elif filing_raw:
                filing_date = str(filing_raw)

            # Map valuation to valuation_usd for scoring
            valuation = self._get_field(attrs, "valuation")
            valuation_usd = None
            if valuation is not None:
                try:
                    valuation_usd = float(valuation)
                except (ValueError, TypeError):
                    pass

            # Parse unit_count if mapped
            unit_count_raw = self._get_field(attrs, "unit_count")
            unit_count = None
            if unit_count_raw is not None:
                try:
                    unit_count = int(unit_count_raw)
                except (ValueError, TypeError):
                    pass

            raw = {
                "permit_number": permit_num,
                "permit_type": self._get_field(attrs, "permit_type") or self.config.get("default_permit_type"),
                "permit_status": self._get_field(attrs, "permit_status") or self.config.get("default_permit_status"),
                "description": description.strip(),
                "address_street": address.strip(),
                "city": self.config["city"],
                "county": self.config["county"],
                "state": "CO",
                "subdivision": self._get_field(attrs, "subdivision"),
                "valuation_usd": valuation_usd,
                "filing_date": filing_date,
                "unit_count": unit_count,
                "contractor_name": self._get_field(attrs, "contractor_name"),
                "latitude": geometry.get("y"),
                "longitude": geometry.get("x"),
            }

            unique_key = f"{self.source_name}_{permit_num or address}"
            records.append(self.make_record(raw, unique_key))

        return records
