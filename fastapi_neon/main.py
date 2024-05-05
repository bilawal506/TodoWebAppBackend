from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, create_engine, Field, select
from fastapi_neon import settings
from typing import Optional, Annotated, List

class User(SQLModel, table=True):
    username:str = Field(index=True)
    uid: Optional[int] = Field(default=None, primary_key=True)

class Mcqs2(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject:str = Field(index=True)
    correctanswer:str
    question: str = Field(index=True)
    option1: str
    option2: str
    option3: str=Field(default=None)
    option4: str=Field(default=None)
    chapter: str

# Database URL adjustment
connection_string = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")

# Create the database engine
engine = create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300)

# Function to create database and tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Lifespan function for table creation
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    create_db_and_tables()
    yield

# FastAPI app initialization with CORS middleware
app = FastAPI(lifespan=lifespan, title="Quix Master API", version="1.0.0",
              servers=[
                  {"url": "https://related-frog-charmed.ngrok-free.app", "description": "Development Server"}
              ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # This now explicitly includes PATCH and DELETE
    allow_headers=["*"],    
)

# Session dependency
def get_session():
    with Session(engine) as session:
        yield session

# Root endpoint
@app.get("/")
def read_root():
    return {"message":"Quizzer"}

# # Create Mcqs
@app.post("/mcqs/", response_model=Mcqs2)
def create_mcq(mcq: Mcqs2, session: Annotated[Session, Depends(get_session)]):
    session.add(mcq)
    session.commit()
    session.refresh(mcq)
    return mcq

# Read Mcqs
@app.get("/mcqs/{subject}/{chapter}", response_model=List[Mcqs2])
def read_mcqs_by_subject(subject: str,chapter:str, session: Annotated[Session, Depends(get_session)]):
    mcqs = session.exec(select(Mcqs2).where(Mcqs2.subject == subject).where(Mcqs2.chapter == chapter)).all()
    return mcqs

# Read MCQs with subject only
@app.get("/mcqs/{subject}", response_model=List[Mcqs2])
def read_mcqs_by_subject(subject: str,session: Annotated[Session, Depends(get_session)]):
    mcqs = session.exec(select(Mcqs2).where(Mcqs2.subject == subject)).all()
    return mcqs

# Update mcq
@app.patch("/mcqs/{mcq_id}", response_model=Mcqs2)
def update_mcq(mcq_id: int, mcq: Mcqs2, session: Annotated[Session, Depends(get_session)]):
    db_mcq = session.get(Mcqs2, mcq_id)
    if not db_mcq:
        raise HTTPException(status_code=404, detail="mcq not found")
    mcq_data = mcq.dict(exclude_unset=True)
    for key, value in mcq_data.items():
        setattr(db_mcq, key, value)
    session.add(db_mcq)
    session.commit()
    session.refresh(db_mcq)
    return db_mcq

@app.get("/privacy")
def privacy_policy():
    return {"This month Fools!!!!":"May"}

# Delete mcq
@app.delete("/mcqs/{mcq_id}", response_model=Mcqs2)
def delete_mcq(mcq_id: int, session: Annotated[Session, Depends(get_session)]):
    db_mcq = session.get(Mcqs2, mcq_id)
    if not db_mcq:
        raise HTTPException(status_code=404, detail="mcq not found")
    session.delete(db_mcq)
    session.commit()
    return db_mcq

# Create User
@app.post("/user/", response_model=User)
def create_user(user: User, session: Annotated[Session, Depends(get_session)]):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Read Users
@app.get("/user/", response_model=List[User])
def read_user(session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(User)).all()
    return user

# Delete User
@app.delete("/user/{user_id}", response_model=User)
def delete_user(user_id: int, session: Annotated[Session, Depends(get_session)]):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(db_user)
    session.commit()
    return db_user