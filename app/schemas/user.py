"""Module containing schemas for user endpoints."""

from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str
    enable_mfa: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class Login2FARequest(BaseModel):
    username: str
    token: str


class DisableMFARequest(BaseModel):
    username: str
    password: str
    token: str  # OTP token for confirmation when disabling MFA
