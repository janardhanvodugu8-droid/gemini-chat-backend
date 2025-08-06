from fastapi import APIRouter, HTTPException, Body, Request
from uuid import uuid4
from app.redis_conn import redis
import json
from datetime import datetime
from app.db_conn import get_conn
from app.tasks.gemini import gemini_reply

# Create router instance with '/chatroom' prefix
router = APIRouter(prefix="/chatroom")

@router.post("/chatrooms/create")
def create_chatroom(request: Request, body: dict = Body(...)):
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Chatroom name is required")

    user_id = request.state.user
    chatroom_id = str(uuid4())
    created_at = datetime.utcnow()

    try:
        conn = get_conn()
        
        #  FORCE AUTOCOMMIT OFF (explicit transaction control)
        conn.autocommit = False
        
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO Chatrooms (id, user_id, name, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (chatroom_id, user_id, name, created_at, created_at)
        )

        conn.commit()
        
        cursor.close()
        conn.close()

        return {"chatroom_id": chatroom_id}

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()  # Rollback on error
        print(" Error during chatroom creation:", e)
        raise HTTPException(status_code=500, detail="Failed to create chatroom")


@router.get("")
def list_chatrooms(request: Request):
    """Get all chatrooms belonging to the authenticated user (with Redis cache)"""
    user_id = request.state.user
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    cache_key = f"chatrooms:{user_id}"

    # Try to return from Redis cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # If not in cache, query DB
    cursor = get_conn().cursor()
    cursor.execute("SELECT id, name FROM Chatrooms WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    chatrooms = [{"id": row[0], "name": row[1]} for row in rows]

    # Store in Redis cache for 5 minutes
    redis.setex(cache_key, 300, json.dumps(chatrooms))

    return chatrooms

@router.get("/{chatroom_id}")
def get_chatroom_detail(request: Request, chatroom_id: str):
    """Get details of a specific chatroom if it belongs to the user"""
    id = request.state.user
    cursor = get_conn().cursor()
    # Verify chatroom exists and belongs to user
    cursor.execute(
        "SELECT id, name FROM Chatrooms WHERE id = %s AND user_id = %s",
        (chatroom_id, id)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    return {"id": row[0], "name": row[1]}

@router.post("/{chatroom_id}/message")
def send_message(request: Request, chatroom_id: str, body: dict = Body(...)):
    """Send a message in a chatroom and trigger AI response"""
    content = body.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")

    user_id = request.state.user
    message_id = str(uuid4())

    conn = None
    cursor = None

    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (id, chatroom_id, sender_type, content) VALUES (%s, %s, %s, %s)",
            (message_id, chatroom_id, 'user', content)
        )
        conn.commit()

        gemini_reply.delay(user_id, chatroom_id, message_id, content)

        return {"message": "Message sent successfully", "message_id": message_id}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

