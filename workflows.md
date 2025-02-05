## What is OTP? 🤔
OTP (One-Time Password) is a time-based password that is valid for a single login session or transaction. Here's a high-level explanation:


## How It Works:
The OTP is generated using a shared secret between the server and the authenticator app (like Google Authenticator). This secret, combined with the current time, creates a temporary password that typically changes every 30 seconds.


## Why It is Secure:
Even if someone knows your static password, they would also need the current OTP (which is valid for a very short period) to access your account. This significantly enhances security by adding an extra layer of verification.


## Simplified Flow Diagrams

- **Simplified Signup / Enable MFA Flow**
    {explain the flow from signup to get the QRCode Image}
    <details>
    <summary>show diagram sequence</summary>

    ```mermaid
    sequenceDiagram
        participant U as Client
        participant S as FastAPI Server
        participant DB as Database (users_db)
        participant T as TwoFactorAuth Class

        U->>S: POST /signup <br>{username, password, enable_mfa: true}
        S->>DB: Check if user exists
        alt User does not exist
            S->>DB: Create user record <br> with password & mfa_enabled true
            S->>T: Initialize TwoFactorAuth(username)
            T-->>S: Generate new secret
            S->>DB: Save mfa_secret (generated secret) in user record
            T->>S: get_provisioning_uri(issuer_name)
            S->>U: Return <br>{message: "Signup successful", mfa_enabled: true, provisioning_uri: URI}
        else
            S-->>U: Return <br> error "User already exists"
        end


        U->>S: POST /qrcode/{username}
        S->>DB: Check User Data and MFA Status
        alt User exist and
            S->>U: Return <br>QRCode Image contain on URI OTP
        else User not exist or MFA is not Enable
            S-->>U: Return <br> error "User already exists or MFA Enable"
        end
    ``` 
    </details>


- **Simplified Login with 2FA Flow**
    {explain the flow from login to get the OTP}
    <details>
    <summary>show diagram sequence</summary>

    ```mermaid
    sequenceDiagram
        participant U as User
        participant S as FastAPI Server
        participant DB as Database (users_db)
        participant T as TwoFactor Class

        U->>S: POST /login <br>{username, password}
        S->>DB: Lookup user record by username
        alt User not found or invalid password
            S-->>U: Return <br>error "Invalid credentials"
        else
            S->>DB: Check mfa_enabled flag
            alt MFA disabled
                S-->>U: Return <br>login success with token (dummy_token_no_mfa)
            else MFA enabled
                S-->>U: Return response "MFA enabled. Please submit OTP" (mfa_required: true)
                U->>S: POST /login-2fa <br>{username, token}
                S->>DB: Retrieve mfa_secret from user record
                S->>T: Instantiate TwoFactor(username, secret)
                T-->>S: Verify OTP via verify_token(token)
                alt OTP valid
                    S-->>U: Return <br>login success with token (dummy_token_with_mfa)
                else OTP invalid
                    S-->>U: Return <br>error "Invalid OTP"
                end
            end
        end
    ```
    </details>

- **Simplified Disable MFA Flow**
    {explain the flow from disable MFA to get the OTP}
    <details>
    <summary>show diagram sequence</summary>

    ```mermaid
    sequenceDiagram
        participant U as User
        participant S as FastAPI Server
        participant DB as Database (users_db)
        participant T as TwoFactor Class

        U->>S: POST /disable-mfa <br>{username, password, token}
        S->>DB: Lookup user by username
        alt User not found
            S-->>U: Return <br>error "User not found"
        else
            S->>DB: Validate password
            alt Incorrect password
                S-->>U: Return <br>error "Incorrect password"
            else
                S->>DB: Check if MFA is enabled
                alt MFA already disabled
                    S-->>U: Return <br>error "MFA is already disabled"
                else
                    S->>T: Instantiate TwoFactor(username, user.mfa_secret)
                    T-->>S: Verify OTP via verify_token(token)
                    alt OTP valid
                        S->>DB: Update user record (set mfa_enabled to false & clear mfa_secret)
                        S-->>U: Return <br>{message: "MFA disabled successfully"}
                    else
                        S-->>U: Return <br>error "Invalid OTP for disabling MFA"
                    end
                end
            end
        end
    ```
    </details>


