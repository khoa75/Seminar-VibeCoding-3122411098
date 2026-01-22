"""
Simple Social Media API - FastAPI Backend

A basic Social Networking Service (SNS) API that allows users to create, retrieve, 
update, and delete posts; add comments; and like/unlike posts.
"""
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
import os

from models import (
    Post, Comment, NewPostRequest, UpdatePostRequest, 
    NewCommentRequest, UpdateCommentRequest, LikeRequest, LikeResponse, Error
)
from database import (
    init_database, get_all_posts, create_post, get_post_by_id, 
    update_post, delete_post, get_comments_by_post_id, create_comment,
    get_comment_by_id, update_comment, delete_comment, add_like, remove_like
)


# Load OpenAPI specification

OPENAPI_YAML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../openapi.yaml'))


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database when application starts."""
    init_database()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Simple Social Media API",
    description="A basic Social Networking Service (SNS) API that allows users to create, retrieve, update, and delete posts; add comments; and like/unlike posts.",
    version="1.0.0",
    contact={
        "name": "Contoso Product Team",
        "email": "support@contoso.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# Add CORS middleware to allow requests from everywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Serve the exact OpenAPI YAML at /openapi.yaml
@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    return FileResponse(OPENAPI_YAML_PATH, media_type="text/yaml")

# Custom Swagger UI that loads the provided openapi.yaml
@app.get("/", include_in_schema=False)
async def custom_swagger_ui():
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
        <style>body { margin: 0; padding: 0; }</style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: '/openapi.yaml',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            });
        };
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content, status_code=200)


# Posts endpoints
@app.get("/api/posts", response_model=List[Post], tags=["Posts"])
async def get_posts():
    """List all posts - Retrieve all recent posts to browse what others are sharing."""
    try:
        return get_all_posts()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.post("/api/posts", response_model=Post, status_code=201, tags=["Posts"])
async def create_new_post(post_data: NewPostRequest):
    """Create a new post - Create a new post to share something with others."""
    try:
        return create_post(post_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.get("/api/posts/{post_id}", response_model=Post, tags=["Posts"])
async def get_post_by_id_endpoint(post_id: str):
    """Get a specific post - Retrieve a specific post by its ID to read in detail."""
    try:
        post = get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found"})
        return post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.patch("/api/posts/{post_id}", response_model=Post, tags=["Posts"])
async def update_post_endpoint(post_id: str, post_data: UpdatePostRequest):
    """Update a post - Update an existing post if you made a mistake or have something to add."""
    try:
        updated_post = update_post(post_id, post_data)
        if not updated_post:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found or you don't have permission to update it"})
        return updated_post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.delete("/api/posts/{post_id}", status_code=204, tags=["Posts"])
async def delete_post_endpoint(post_id: str):
    """Delete a post - Delete a post if you no longer want it shared."""
    try:
        deleted = delete_post(post_id)
        if not deleted:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found"})
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


# Comments endpoints
@app.get("/api/posts/{post_id}/comments", response_model=List[Comment], tags=["Comments"])
async def get_comments_by_post_id_endpoint(post_id: str):
    """List comments for a post - Retrieve all comments on a specific post."""
    try:
        # Check if post exists
        if not get_post_by_id(post_id):
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found"})
        return get_comments_by_post_id(post_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.post("/api/posts/{post_id}/comments", response_model=Comment, status_code=201, tags=["Comments"])
async def create_comment_endpoint(post_id: str, comment_data: NewCommentRequest):
    """Create a comment - Add a comment to a post to share your thoughts."""
    try:
        comment = create_comment(post_id, comment_data)
        if not comment:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found"})
        return comment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.get("/api/posts/{post_id}/comments/{comment_id}", response_model=Comment, tags=["Comments"])
async def get_comment_by_id_endpoint(post_id: str, comment_id: str):
    """Get a specific comment - Retrieve a specific comment by its ID."""
    try:
        comment = get_comment_by_id(post_id, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Comment not found"})
        return comment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.patch("/api/posts/{post_id}/comments/{comment_id}", response_model=Comment, tags=["Comments"])
async def update_comment_endpoint(post_id: str, comment_id: str, comment_data: UpdateCommentRequest):
    """Update a comment - Update an existing comment to correct or revise it."""
    try:
        updated_comment = update_comment(post_id, comment_id, comment_data)
        if not updated_comment:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Comment not found or you don't have permission to update it"})
        return updated_comment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.delete("/api/posts/{post_id}/comments/{comment_id}", status_code=204, tags=["Comments"])
async def delete_comment_endpoint(post_id: str, comment_id: str):
    """Delete a comment - Delete a comment if necessary."""
    try:
        deleted = delete_comment(post_id, comment_id)
        if not deleted:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Comment not found"})
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


# Likes endpoints
@app.post("/api/posts/{post_id}/likes", response_model=LikeResponse, status_code=201, tags=["Likes"])
async def like_post_endpoint(post_id: str, like_data: LikeRequest):
    """Like a post - Like a post to show appreciation."""
    try:
        liked_at = add_like(post_id, like_data.username)
        if liked_at is None:
            # Check if post exists
            if not get_post_by_id(post_id):
                raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Post not found"})
            else:
                raise HTTPException(status_code=400, detail={"error": "VALIDATION_ERROR", "message": "Post already liked by this user"})
        
        return LikeResponse(
            postId=post_id,
            username=like_data.username,
            likedAt=liked_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


@app.delete("/api/posts/{post_id}/likes", status_code=204, tags=["Likes"])
async def unlike_post_endpoint(post_id: str, username: str = Query(..., description="Username of the user removing the like")):
    """Unlike a post - Remove your like from a post if you change your mind."""
    try:
        deleted = remove_like(post_id, username)
        if not deleted:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Like not found"})
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
