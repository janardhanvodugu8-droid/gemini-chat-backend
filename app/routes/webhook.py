# Check this api in stripe 

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe
from app.config import STRIPE_WEBHOOK_SECRET  
from app.db_conn import get_conn  

router = APIRouter(prefix="/webhook")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    # Handle different event types
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")

        if not user_id:
            print(" No user_id found in metadata")
        else:
            with get_conn().cursor() as cur:
                cur.execute(
                    "UPDATE Users SET subscription_tier = 'Pro' WHERE id = %s",
                    ( user_id,)
                )
                get_conn().commit()

    elif event_type == "payment_intent.succeeded":
        print(" Payment succeeded:", data["id"])

    elif event_type == "payment_intent.payment_failed":
        print(" Payment failed:", data["id"])

    return JSONResponse(status_code=200, content={"status": "success"})

