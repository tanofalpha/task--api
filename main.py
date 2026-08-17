from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import init_db, get_connection


app = FastAPI()

init_db()


class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# GET all tasks
@app.get("/tasks")
def get_tasks():
    conn = get_connection()

    rows = conn.execute(
        "SELECT id, title, done FROM tasks"
    ).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]


# GET one task
@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_connection()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


# Create a task
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if task.title is None or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"}
        )

    conn = get_connection()

    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, False)
    )

    conn.commit()

    new_id = cursor.lastrowid

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (new_id,)
    ).fetchone()

    conn.close()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


# Update a task
@app.put("/tasks/{id}")
def update_task(id: int, updated_task: TaskUpdate):

    conn = get_connection()

    # First check whether the task exists
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (id,)
    ).fetchone()

    if row is None:
        conn.close()

        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    # Keep the old values if they weren't provided
    new_title = (
        updated_task.title
        if updated_task.title is not None
        else row["title"]
    )

    new_done = (
        updated_task.done
        if updated_task.done is not None
        else bool(row["done"])
    )

    conn.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (new_title, new_done, id)
    )

    conn.commit()

    updated_row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "done": bool(updated_row["done"])
    }


# Delete a task
@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):

    conn = get_connection()

    cursor = conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (id,)
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    return None