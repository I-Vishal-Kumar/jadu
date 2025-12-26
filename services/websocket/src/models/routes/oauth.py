"""OAuth routes for service authentication."""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import httpx
from datetime import datetime, timedelta

from ...config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oauth", tags=["oauth"])

# OAuth configuration from settings
settings = get_settings()

ZOHO_CLIENT_ID = settings.zoho_client_id
ZOHO_CLIENT_SECRET = settings.zoho_client_secret
ZOHO_REDIRECT_URI = settings.zoho_redirect_uri

ZOOM_CLIENT_ID = settings.zoom_client_id
ZOOM_CLIENT_SECRET = settings.zoom_client_secret
ZOOM_REDIRECT_URI = settings.zoom_redirect_uri

GITHUB_CLIENT_ID = settings.github_client_id
GITHUB_CLIENT_SECRET = settings.github_client_secret
GITHUB_REDIRECT_URI = settings.github_redirect_uri


class ServiceStatusResponse(BaseModel):
    """Response model for service connection status."""
    zoho: bool
    zoom: bool
    github: bool


@router.get("/{service}/init")
async def oauth_init(service: str, user_id: str = Query("test-user")):
    """Initiate OAuth flow by redirecting to service provider."""
    
    if service == "zoho":
        if not ZOHO_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Zoho OAuth not configured. Set ZOHO_CLIENT_ID in .env")
        
        auth_url = (
            f"https://accounts.zoho.com/oauth/v2/auth"
            f"?client_id={ZOHO_CLIENT_ID}"
            f"&response_type=code"
            f"&redirect_uri={ZOHO_REDIRECT_URI}"
            f"&scope=ZohoMail.messages.ALL,ZohoCliq.Channels.ALL,ZohoCliq.Messages.ALL"
            f"&access_type=offline"
            f"&state={user_id}"  # Pass user_id in state
        )
        return RedirectResponse(url=auth_url)
    
    elif service == "zoom":
        if not ZOOM_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Zoom OAuth not configured. Set ZOOM_CLIENT_ID in .env")
        
        auth_url = (
            f"https://zoom.us/oauth/authorize"
            f"?client_id={ZOOM_CLIENT_ID}"
            f"&response_type=code"
            f"&redirect_uri={ZOOM_REDIRECT_URI}"
            f"&state={user_id}"
        )
        return RedirectResponse(url=auth_url)
    
    elif service == "github":
        if not GITHUB_CLIENT_ID:
            raise HTTPException(status_code=500, detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in .env")
        
        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={GITHUB_CLIENT_ID}"
            f"&redirect_uri={GITHUB_REDIRECT_URI}"
            f"&scope=repo,user"
            f"&state={user_id}"
        )
        return RedirectResponse(url=auth_url)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")


@router.get("/{service}/callback")
async def oauth_callback(
    service: str, 
    code: str, 
    state: str = "test-user",
    location: str = Query(None),
    accounts_server: str = Query(None, alias="accounts-server")
):
    """Handle OAuth callback and exchange code for tokens."""
    
    user_id = state  # Extract user_id from state parameter
    
    try:
        if service == "zoho":
            # Use regional accounts server if provided
            token_url = f"{accounts_server or 'https://accounts.zoho.com'}/oauth/v2/token"
            
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "code": code,
                        "client_id": ZOHO_CLIENT_ID,
                        "client_secret": ZOHO_CLIENT_SECRET,
                        "redirect_uri": ZOHO_REDIRECT_URI,
                        "grant_type": "authorization_code"
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)
                
                # Store in database - use direct import
                from intellibooks_db.database.connection import get_db_pool
                from intellibooks_db.database.repositories.credential_repo import CredentialRepository
                
                pool = await get_db_pool()
                if pool:
                    repo = CredentialRepository(pool)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    await repo.save(
                        user_id=user_id,
                        service_name="zoho",
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                        scope=token_data.get("scope", "")
                    )
                    logger.info(f"Stored Zoho credentials for user {user_id}")
        
        elif service == "zoom":
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://zoom.us/oauth/token",
                    data={
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": ZOOM_REDIRECT_URI
                    },
                    auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)
                
                # Store in database - use direct import
                from intellibooks_db.database.connection import get_db_pool
                from intellibooks_db.database.repositories.credential_repo import CredentialRepository
                
                pool = await get_db_pool()
                if pool:
                    repo = CredentialRepository(pool)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    await repo.save(
                        user_id=user_id,
                        service_name="zoom",
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                        scope=token_data.get("scope", "")
                    )
                    logger.info(f"Stored Zoom credentials for user {user_id}")
        
        elif service == "github":
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "code": code,
                        "client_id": GITHUB_CLIENT_ID,
                        "client_secret": GITHUB_CLIENT_SECRET,
                        "redirect_uri": GITHUB_REDIRECT_URI
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                
                if not access_token:
                    raise HTTPException(status_code=400, detail=f"No access token in response: {token_data}")
                
                # Store in database - use direct import
                from intellibooks_db.database.connection import get_db_pool
                from intellibooks_db.database.repositories.credential_repo import CredentialRepository
                
                pool = await get_db_pool()
                if pool:
                    repo = CredentialRepository(pool)
                    await repo.save(
                        user_id=user_id,
                        service_name="github",
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=None,
                        scope=token_data.get("scope", "")
                    )
                    logger.info(f"Stored GitHub credentials for user {user_id}")
        
        # Redirect back to dashboard on frontend port
        return RedirectResponse(url=f"http://localhost:3001/dashboard/v2?auth_success={service}")
    
    except Exception as e:
        logger.error(f"OAuth callback error for {service}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_oauth_status(user_id: str = Query("test-user")):
    """Get connection status for all services."""
    try:
        # Use direct imports to avoid __init__ issues
        from intellibooks_db.database.connection import get_db_pool
        from intellibooks_db.database.repositories.credential_repo import CredentialRepository
        
        pool = await get_db_pool()
        if not pool:
            return ServiceStatusResponse(zoho=False, zoom=False, github=False)
        
        repo = CredentialRepository(pool)
        
        zoho = await repo.get(user_id, "zoho")
        zoom = await repo.get(user_id, "zoom")
        github = await repo.get(user_id, "github")
        
        return ServiceStatusResponse(
            zoho=bool(zoho and zoho.get('access_token')),
            zoom=bool(zoom and zoom.get('access_token')),
            github=bool(github and github.get('access_token'))
        )
    except Exception as e:
        logger.error(f"Failed to get OAuth status: {e}")
        return ServiceStatusResponse(zoho=False, zoom=False, github=False)
