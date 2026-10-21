
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer


# Secret key: JWT token ko sign aur verify karne ke liye
SECRET_KEY = "mysecret"

# JWT signing algorithm
ALGORITHM = "HS256"

# Token kitne minutes tak valid rahega
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Login endpoint se token receive karne ke liye OAuth2 scheme
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")


# JWT token create karne ka function
def token_create(data: dict):
    # Original data ki copy banana
    to_encode = data.copy()

    # Current UTC time mein 30 minutes add karke expiry set karna
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Token ke payload mein expiry time add karna
    to_encode.update({"exp": expire})

    # Data ko secret key se sign karke JWT token return karna
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# JWT token verify karne ka function
def verify_token(token: str = Depends(oauth2_schema)):
    try:
        # Token ki signature aur expiry verify karke payload decode karna
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Valid token ka payload return karna
        return payload

    except JWTError:
        # Token invalid ya expired hone par 401 error dena
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
          
        )
