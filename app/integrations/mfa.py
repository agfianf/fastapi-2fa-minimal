"""Handle Multi-Factor Authentication (MFA) using PyOTP."""

from io import BytesIO

import pyotp
import qrcode


class TwoFactor:
    def __init__(self, username: str, secret: str = None):
        self.username = username
        # If no secret is provided, generate a new secret.
        self.secret = secret if secret is not None else pyotp.random_base32()

    def get_provisioning_uri(self, issuer_name: str = "FastAPIApp") -> str:
        totp = pyotp.TOTP(self.secret)
        uri_otp = totp.provisioning_uri(
            name=self.username,
            issuer_name=issuer_name,
        )
        return uri_otp

    def get_provisioning_qrcode(self, issuer_name: str = "FastAPIApp") -> bytes:
        """
        Generate a QR Code as image bytes from the provisioning URI.
        This QR code can be displayed to the user for scanning in an authenticator app.
        """
        uri_otp = self.get_provisioning_uri(issuer_name)
        img = qrcode.make(uri_otp)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    def verify_token(self, token: str) -> bool:
        totp = pyotp.TOTP(self.secret)
        return totp.verify(token)
