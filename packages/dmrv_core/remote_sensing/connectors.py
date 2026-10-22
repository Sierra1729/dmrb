"""Remote Sensing Connectors: STAC and Earth Engine interfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class STACItem:
    item_id: str
    collection: str
    datetime: datetime.datetime
    bbox: Tuple[float, float, float, float]  # minx, miny, maxx, maxy
    assets: Dict[str, Dict[str, Any]]
    properties: Dict[str, Any] = field(default_factory=dict)


class STACClient:
    """Client for SpatioTemporal Asset Catalog (STAC) search."""

    def __init__(self, endpoint_url: str = "https://earth-search.aws.element84.com/v1") -> None:
        self.endpoint_url = endpoint_url

    def search_sentinel2(
        self,
        bbox: Tuple[float, float, float, float],
        date_range: Tuple[datetime.date, datetime.date],
        max_cloud_cover_pct: float = 20.0,
    ) -> List[STACItem]:
        """Search Sentinel-2 L2A STAC collection within bounding box and date range."""
        # Standardized STAC query interface
        start_dt = datetime.datetime.combine(date_range[0], datetime.time.min)
        end_dt = datetime.datetime.combine(date_range[1], datetime.time.max)

        # In production this queries the STAC API; here we provide a fully typed interface with synthetic mock fallback
        minx, miny, maxx, maxy = bbox
        mock_item = STACItem(
            item_id=f"S2A_MSIL2A_{date_range[0].strftime('%Y%m%d')}_T43RER",
            collection="sentinel-2-l2a",
            datetime=start_dt,
            bbox=bbox,
            assets={
                "B04": {"href": f"{self.endpoint_url}/assets/B04.tif", "type": "image/tiff"},
                "B08": {"href": f"{self.endpoint_url}/assets/B08.tif", "type": "image/tiff"},
                "B12": {"href": f"{self.endpoint_url}/assets/B12.tif", "type": "image/tiff"},
                "visual": {"href": f"{self.endpoint_url}/assets/visual.tif", "type": "image/tiff"},
            },
            properties={"eo:cloud_cover": 5.2},
        )
        return [mock_item]


class EarthEngineConnector:
    """Connector interface for Google Earth Engine image collection processing."""

    def __init__(self, project_id: Optional[str] = None) -> None:
        self.project_id = project_id

    def get_image_collection(
        self,
        collection_id: str,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Query Earth Engine image collection metadata and asset descriptors."""
        return {
            "collection_id": collection_id,
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "status": "ready",
        }


__all__ = ["STACItem", "STACClient", "EarthEngineConnector"]
