from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Optional, Any


class BiddingInfo(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    publish_date: str
    created_at: Optional[str] = None
    is_good: Optional[bool] = None
    # Additional optional fields
    organization: Optional[str] = None
    budget: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    expected_time: Optional[str] = None
    remarks: Optional[str] = None
    url: Optional[str] = None

    # Serialize _id with the original key name
    @field_serializer('id')
    def serialize_id(self, id: Optional[str], _info) -> Optional[str]:
        return id

    # Custom serialization to include _id in the output
    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(by_alias=True, exclude_none=True, **kwargs)
        # Only include _id if it has a value
        if self.id is not None:
            data['_id'] = self.id
        # Ensure _id is not in data if it's None (MongoDB will auto-generate)
        elif '_id' in data:
            del data['_id']
        return data

