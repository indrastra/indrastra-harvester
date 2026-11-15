from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.repositories.security import validate_public_http_endpoint


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    endpoint: str = Field(min_length=8, max_length=2048)
    description: str | None = Field(default=None, max_length=10000)
    organization: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    contact_email: str | None = Field(default=None, max_length=320)
    validate_endpoint: bool = True

    @field_validator("endpoint")
    @classmethod
    def endpoint_must_be_public_http(cls, value: str) -> str:
        return validate_public_http_endpoint(value)


class RepositoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    organization: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    contact_email: str | None = Field(default=None, max_length=320)
    is_enabled: bool | None = None

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    endpoint: str
    description: str | None
    organization: str | None
    country: str | None
    contact_email: str | None
    is_enabled: bool
    validation_status: str
    oai_repository_name: str | None
    admin_email: str | None
    earliest_datestamp: str | None
    deleted_record: str | None
    granularity: str | None
    metadata_formats: list
    sets: list
    last_validation_error: str | None
    last_validated_at: datetime | None
    created_at: datetime
    updated_at: datetime
