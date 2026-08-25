from pydantic import BaseModel

class SignUpRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: str = None
    mobile_number: str = None
    role: str = "USER"

