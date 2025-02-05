"""Main FastAPI application file."""

import io

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from integrations.mfa import TwoFactor
from schemas.user import DisableMFARequest, Login2FARequest, LoginRequest, SignupRequest

app = FastAPI()

# Simulated database for users
users_db = {}


@app.get("/users")
def get_users():
    return users_db


# Endpoint to serve the QR Code image.
@app.get("/qrcode/{username}")
def get_qrcode_for_scan(username: str):
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="QR Code not available")

    if not user["mfa_enabled"] or not user["mfa_secret"]:
        raise HTTPException(status_code=400, detail="MFA is not enabled for this user")

    # Create a TwoFactor instance and generate the QR code image bytes.
    twofa = TwoFactor(username=username, secret=user["mfa_secret"])
    qr_image_bytes = twofa.get_provisioning_qrcode()
    return StreamingResponse(io.BytesIO(qr_image_bytes), media_type="image/png")


# Endpoint for user signup/registration.
@app.post("/auth/sign-up")
def signup(data: SignupRequest) -> dict:
    if data.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    # Store basic user data
    user_data = {
        "password": data.password,  # In production, make sure to hash passwords.
        "mfa_enabled": data.enable_mfa,
        "mfa_secret": None,
    }

    provisioning_uri = None
    if data.enable_mfa:
        # Initialize 2FA for the user (generate secret)
        twofa = TwoFactor(username=data.username)
        user_data["mfa_secret"] = twofa.secret
        provisioning_uri = twofa.get_provisioning_uri()

    # Save user data in the simulated database
    users_db[data.username] = user_data

    return {
        "message": "Signup successful",
        "mfa_enabled": data.enable_mfa,
        "provisioning_uri": provisioning_uri,
    }


# Endpoint for login (credential verification).
@app.post("/auth/sign-in")
def login(data: LoginRequest):
    user = users_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # If the user has enabled MFA, instruct to submit OTP
    if user["mfa_enabled"]:
        return {
            "message": "MFA enabled. Please submit OTP to complete login.",
            "mfa_required": True,
        }
    else:
        # Generate token/session for user (dummy token here)
        return {"message": "Login successful", "token": "dummy_token_no_mfa"}


# Endpoint for OTP verification during login.
@app.post("/auth/sign-in-2fa")
def login_2fa(data: Login2FARequest):
    user = users_db.get(data.username)
    if not user or not user["mfa_enabled"]:
        raise HTTPException(
            status_code=400,
            detail="User not found or MFA is not enabled",
        )

    # Create a TwoFactor instance using the stored secret
    twofa = TwoFactor(username=data.username, secret=user["mfa_secret"])
    if twofa.verify_token(data.token):
        return {"message": "Login successful", "token": "dummy_token_with_mfa"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")


# Endpoint to disable MFA.
@app.delete("/auth/disable-mfa")
def disable_mfa(data: DisableMFARequest):
    user = users_db.get(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["password"] != data.password:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if not user["mfa_enabled"]:
        raise HTTPException(status_code=400, detail="MFA is already disabled")

    # Verify OTP as an extra confirmation for disabling MFA
    twofa = TwoFactor(username=data.username, secret=user["mfa_secret"])
    if not twofa.verify_token(data.token):
        raise HTTPException(status_code=400, detail="Invalid OTP for disabling MFA")

    # Disable MFA: update user data
    user["mfa_enabled"] = False
    user["mfa_secret"] = None

    return {"message": "MFA disabled successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
