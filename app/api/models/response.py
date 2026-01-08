from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class UniversityInfo(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    publish_date: str
    created_at: Optional[str] = None
    url: Optional[str] = None