from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

class PricingModelEnum(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"

class SourceMetadata(BaseModel):
    name: str = Field(..., description="Name of the source site")
    url: str = Field(..., description="Original extracted URL resource")

class StartupEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source: SourceMetadata
    entityName: str = Field(..., alias="content.entityName")
    employeeCount: Optional[int] = Field(None, alias="content.data.employeeCount")
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source: SourceMetadata
    startupName: str = Field(..., alias="content.startupName")
    pricingModel: PricingModelEnum = Field(..., alias="content.pricingModel")
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResearchPaperEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    title: str = Field(..., alias="content.title")
    authors: List[str] = Field(..., alias="content.authors")
    paperUrl: str = Field(..., alias="content.paper_url")
    githubUrl: Optional[str] = Field(None, alias="content.github_url")
    githubStars: Optional[int] = Field(0, alias="content.github_stars")
    publishedDate: datetime = Field(..., alias="content.published_date")

class JobEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    source: SourceMetadata
    company: str = Field(..., alias="content.company")
    title: str = Field(..., alias="content.title")
    date: datetime = Field(..., alias="content.date")
    isRemote: bool = Field(default=True, alias="content.is_remote")
    roleFamily: str = Field(default="Engineering", alias="content.role_family")

class NewsEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: str = "1.0"
    recordType: str = "NEWS"
    source: SourceMetadata
    title: str = Field(..., alias="content.title")
    publishedAt: datetime = Field(..., alias="content.published_at")
    summary: Optional[str] = Field(None, alias="content.summary")

