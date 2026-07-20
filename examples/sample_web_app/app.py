"""A sample FastAPI web application with database, cache, and auth."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Simulated database and cache
db = {"users": [], "posts": []}
cache = {}

def authenticate(token: str):
    """Verify JWT token."""
    return token == "valid_token"

@app.get("/api/users")
def get_users():
    if "users" in cache:
        return cache["users"]
    result = db["users"]
    cache["users"] = result
    return result

@app.post("/api/users")
def create_user(name: str, email: str):
    user = {"name": name, "email": email}
    db["users"].append(user)
    cache.pop("users", None)
    return user

@app.get("/api/posts")
def get_posts():
    return db["posts"]

@app.post("/api/posts")
def create_post(title: str, body: str):
    post = {"title": title, "body": body}
    db["posts"].append(post)
    return post

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int):
    db["posts"].pop(post_id, None)
    return {"status": "deleted"}
