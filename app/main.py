from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app import schema, model
from app.model import RoleEnum

app = FastAPI(title="User Management API")

Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/login")
def login(user_data: schema.UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(model.User)
        .filter(
            model.User.email == user_data.email,
            model.User.password == user_data.password
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Crendial"
        )

    return {
        "message":"User Loged in successfully",
        "data":user
    }


# CREATE USER (Signup)
@app.post(
    "/users", response_model=schema.UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user_data: schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(model.User).filter(model.User.email == user_data.email).first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    new_user = model.User(
        email=user_data.email,
        password=user_data.password,  # hash later
        role=RoleEnum.user,  # always default user
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# GET ALL USERS
@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(model.User).all()
    return {"message": "Users fetched successfully", "count": len(users), "data": users}


# UPDATE USER
@app.put("/users/{user_id}", response_model=schema.UserResponse)
def update_user(
    user_id: int, update_data: schema.UserUpdate, db: Session = Depends(get_db)
):
    user = db.query(model.User).filter(model.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


# Delete User
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    db.delete(user)
    db.commit()

    return None


# get user by id
@app.get("/users/{user_id}", response_model=schema.UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.id == user_id).first()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not Found"
        )
    return user
