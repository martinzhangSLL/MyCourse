from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str  # 管理员用 "admin"，教师用教师姓名
    password: str
    role: str  # "admin" or "teacher"


class UserResponse(BaseModel):
    id: int
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
