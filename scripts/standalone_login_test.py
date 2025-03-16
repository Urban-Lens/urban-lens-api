#!/usr/bin/env python
"""
Standalone FastAPI app with just the login endpoint for testing
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

app = FastAPI()

# Define login request model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/login", response_model=Token)
async def login_for_access_token(login_data: LoginRequest):
    """Login endpoint for testing"""
    print(f"Received login request: {login_data}")
    
    # For testing, just check for a test user
    if login_data.email == "user@example.com" and login_data.password == "Password2@":
        return {"access_token": "mock_token_12345", "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/")
async def root():
    """Root endpoint for testing connectivity"""
    return {"message": "Login test server is running"}

if __name__ == "__main__":
    print("Starting standalone login test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 