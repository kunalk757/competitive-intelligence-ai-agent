import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.services.company_service import (
    company_data_service,
    CompanyDetailsResponse,
)

logger = logging.getLogger("companies_routes")

router = APIRouter(prefix="/companies", tags=["Companies"])


class BatchRefreshResponse(BaseModel):
    success: bool
    message: str
    total_companies: int
    successful_count: int
    failed_count: int
    successful_companies: List[str]
    failed_companies: List[Dict[str, Any]]
    timestamp: str


@router.post("/refresh-all", response_model=BatchRefreshResponse)
async def refresh_all_companies_endpoint():
    """
    Automated batch trigger endpoint to refresh intelligence & news
    for all 20 tracked companies.
    Invoked by Google Apps Script / Cloud Schedulers (10:00 AM & 10:00 PM IST).
    """
    try:
        result = await company_data_service.refresh_all_companies()
        return result
    except Exception as e:
        logger.error(f"Error during batch refresh of all companies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute batch company refresh: {str(e)}",
        )


@router.get("/{company_name}", response_model=CompanyDetailsResponse)
async def get_company_details_endpoint(
    company_name: str,
    refresh: bool = Query(
        default=False,
        description="Force bypass of cache to fetch fresh data from Tavily and GNews."
    ),
):
    """
    Retrieve real-time company intelligence (Tavily overview + GNews articles)
    with automatic persistent caching.
    """
    if not company_name or not company_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name parameter must not be empty.",
        )

    try:
        details = await company_data_service.get_company_details(
            company_name=company_name, force_refresh=refresh
        )
        return details
    except Exception as e:
        logger.error(f"Error fetching company details for '{company_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve company details: {str(e)}",
        )


@router.post("/{company_name}/refresh", response_model=CompanyDetailsResponse)
async def refresh_company_details_endpoint(company_name: str):
    """
    Explicitly trigger fresh Tavily + GNews sync for a company and update persistent cache.
    Can be invoked by UI manual refresh or automated cloud schedulers.
    """
    if not company_name or not company_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name parameter must not be empty.",
        )

    try:
        details = await company_data_service.get_company_details(
            company_name=company_name, force_refresh=True
        )
        return details
    except Exception as e:
        logger.error(f"Error refreshing company details for '{company_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh company details: {str(e)}",
        )
