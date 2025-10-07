from fastapi import APIRouter, Request, Header, HTTPException
import hmac, hashlib, os
import httpx
from app.config import settings

router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
API_BASE = os.getenv("API_BASE","http://localhost:8000")

def verify_signature(raw_body: bytes, signature: str) -> bool:
    if not signature or not APP_SECRET:
        return False
    expected = hmac.new(APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.get("/webhook")
async def verify_token(mode: str = None, challenge: str = None, verify_token: str = None):
    """Webhook verification endpoint for Meta"""
    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=400, detail="Verification failed")

@router.post("/webhook")
async def inbound(request: Request, x_hub_signature_256: str = Header(None)):
    raw = await request.body()
    if not verify_signature(raw, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    # parse message
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            messages = val.get("messages", [])
            for msg in messages:
                phone = msg["from"]
                text = msg.get("text", {}).get("body", "")
                # optional: map phone -> employee profile lookup
                # call internal /ask endpoint
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{API_BASE}/ask",
                        json={"question": text, "top_k": 5},
                        headers={"x-api-key": os.getenv("API_KEY")}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        out_text = data.get("answer") + "\n\n" + f"Source: {data.get('citations', [{}])[0].get('doc_id','')}"
                    else:
                        out_text = "Sorry, something went wrong. Please contact HR: hr@company.com"

                # send back via WhatsApp send API
                send_url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
                body = {
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": out_text}
                }
                headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                await client.post(send_url, json=body, headers=headers)
    return {"status":"processed"}
