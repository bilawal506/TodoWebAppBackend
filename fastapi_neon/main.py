from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, create_engine, Field, select, update, delete
from fastapi_neon import settings
from typing import Optional, Annotated, List

# Define the Todo modela
class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
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
app = FastAPI(lifespan=lifespan, title="Todo API", version="1.0.0",
              servers=[
                  {"url": "https://related-frog-charmed.ngrok-free.app/", "description": "Development Server"}
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
    return {"Todo App!"}

# Create Todo
@app.post("/todos/", response_model=Todo)
def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

# Read Todos
@app.get("/todos/", response_model=List[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    return todos

# Update Todo
@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: Todo, session: Annotated[Session, Depends(get_session)]):
    db_todo = session.get(Todo, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo_data = todo.dict(exclude_unset=True)
    for key, value in todo_data.items():
        setattr(db_todo, key, value)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

# Delete Todo
@app.delete("/todos/{todo_id}", response_model=Todo)
def delete_todo(todo_id: int, session: Annotated[Session, Depends(get_session)]):
    db_todo = session.get(Todo, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(db_todo)
    session.commit()
    return db_todo
