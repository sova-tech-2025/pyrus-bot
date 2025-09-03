import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import json

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
    task = json.loads(body)["task"]
    comment = task["comments"][-1]
    comment_author = comment["author"]
    author_name = comment_author["first_name"] + " " + comment_author["last_name"]
    comment_text = "Hello, {}! You said: {}".format(author_name, comment["text"])
    return "{{ \"text\":\"{}\", \"reassign_to\":{{ \"id\":{} }} }}".format(comment_text, comment_author["id"])

@app.get("/health")
async def health():
    return {"status": "ok"}
