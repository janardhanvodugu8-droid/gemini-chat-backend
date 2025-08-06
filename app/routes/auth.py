from fastapi import APIRouter, HTTPException, Body
from uuid import uuid4
import random
from app.jwt_utils import create_token
from app.services.otp_service import store_otp, verify_stored_otp
from app.db_conn import get_conn

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup(body: dict = Body(...)):
    mobile_number = body.get("mobile_number")
    if not mobile_number:
        return {"error": "mobile_number is required"}

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Users WHERE mobile_number = %s", (mobile_number,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        return {"user_id": existing_user[0], "mobile_number": mobile_number, "message": "User already registered"}

    user_id = str(uuid4())
    cursor.execute(
        "INSERT INTO Users (id, mobile_number) VALUES (%s, %s)",
        (user_id, mobile_number)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"user_id": user_id, "mobile_number": mobile_number, "message": "User registered"}

@router.post("/send-otp")
def send_otp(body: dict = Body(...)):
    mobile_number = body.get("mobile_number")
    if not mobile_number:
        raise HTTPException(status_code=400, detail="mobile_number is required")

    otp = str(random.randint(1000, 9999))
    store_otp(mobile_number, otp)

    # ⚠️ Remove this line in production:
    return {"otp": otp}
    # In production: return {"message": "OTP sent to your mobile number."}

@router.post("/verify-otp")
def verify_otp(body: dict = Body(...)):
    mobile_number = body.get("mobile_number")
    otp = body.get("otp")

    if not mobile_number or not otp:
        raise HTTPException(status_code=400, detail="mobile_number and otp are required")

    if verify_stored_otp(mobile_number, otp):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE mobile_number = %s", (mobile_number,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")

        token = create_token({"sub": user[0]})
        cursor.close()
        conn.close()
        return {"token": token}

    raise HTTPException(status_code=401, detail="Invalid OTP")

@router.post("/forgot-password")
def forgot_password(body: dict = Body(...)):
    mobile_number = body.get("mobile_number")
    if not mobile_number:
        raise HTTPException(status_code=400, detail="mobile_number is required")

    otp = str(random.randint(1000, 9999))
    store_otp(mobile_number, otp)

    # ⚠️ Remove in production
    return {"otp": otp, "message": "Use this OTP to reset password."}
    # In production: return {"message": "OTP sent to your mobile number."}
