import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import json

from app.service.check import handle_form_mutation

load_dotenv()
app = FastAPI()

# env
SECRET_KEY = os.getenv("BOT_SECRET_KEY")

@app.post("/")
async def index(request: Request, x_pyrus_sig: str = Header(...)):
    body = await request.body()
    secret = SECRET_KEY.encode()

    if not _is_signature_correct(body, secret, x_pyrus_sig):
        raise HTTPException(status_code=400, detail="Invalid signature")

    return _prepare_response(body.decode("utf-8"))


def _is_signature_correct(message: bytes, secret: bytes, signature: str) -> bool:
    digest = hmac.new(secret, msg=message, digestmod=hashlib.sha1).hexdigest()
    return hmac.compare_digest(digest, signature.lower())


def _prepare_response(body: str):
    print(body)
    ctx = {}
    task = json.loads(body)["task"]
    ctx.access_token = task["access_token"]

    if json.loads(body).get("event") == "comment" and task.get("form_id") == 2336661 and task.get("current_step") == 1:
        handle_form_mutation(task, ctx)
        # Подготовить ответ
        comment = task["comments"][-1]
        comment_author = comment.get("author", {})
        return {
            "text": f"Изменение формы",
            "reassign_to": {"id": comment_author.get("id")}
        }


    # Подготовить ответ
    comment = task["comments"][-1]
    comment_author = comment.get("author", {})
    author_name = f'{comment_author.get("first_name", "")} {comment_author.get("last_name", "")}'.strip()
    comment_text = comment.get("text", "[no text]")
    return {
        "text": f"Hello, {author_name}! You said: {comment_text}",
        "reassign_to": {"id": comment_author.get("id")}
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
