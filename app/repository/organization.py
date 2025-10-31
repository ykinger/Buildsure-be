
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.organization import Organization

async def create_organization(organization: Organization, session: AsyncSession = Depends(get_db)) -> Organization:
    session.add(organization)
    await session.commit()
    await session.refresh(organization)
    return organization

async def get_organization_by_id(organization_id: str, session: AsyncSession = Depends(get_db)) -> Organization:
    statement = select(Organization).where(Organization.id == organization_id)
    result = await session.execute(statement)
    organization = result.scalar_one_or_none()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization

async def list_organizations(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[Organization]:
    statement = select(Organization).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_organization(organization_id: str, organization_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[Organization]:
    organization = await get_organization_by_id(organization_id, session)
    if organization:
        for key, value in organization_data.items():
            setattr(organization, key, value)
        session.add(organization)
        await session.commit()
        await session.refresh(organization)
        return organization
    return None

async def delete_organization(organization_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    organization = await get_organization_by_id(organization_id, session)
    if organization:
        await session.delete(organization)
        await session.commit()
        return True
    return False
