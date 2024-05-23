from datetime import datetime

from pydantic import BaseModel, Field


class GrayLineNotFound(Exception):
    def __init__(self):
        super().__init__("Gray line not found")


class BLAZ(BaseModel):
    status: str
    message: str
    reference: str = Field(max_length=16, min_length=16)
    date: datetime
    receiver: str
    sender: str
    amount: str
