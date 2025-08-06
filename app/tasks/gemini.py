
import uuid
from app.config import celery_app  
from app.genai import send_to_gemini
from app.db_conn import get_conn

@celery_app.task(bind=True, name='gemini_reply')
def gemini_reply(self, user_id: str, chatroom_id: str, message_id: str, prompt: str):
    try:

        # print(f" Prompt to Gemini: {prompt}")
        gemini_reply = send_to_gemini(prompt)

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (id, chatroom_id, sender_type, content) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), chatroom_id, 'gemini', gemini_reply)
        )
        conn.commit()

        return {"status": "success", "chatroom_id": chatroom_id}

    except Exception as db_error:
        if conn:
            conn.rollback()
        raise self.retry(countdown=60, max_retries=3, exc=db_error)

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()