from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

with open("database", "r") as f:
    tasks = json.load(f)


class TaskCreate(BaseModel):
    title: str


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


@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {id} not found"
    )


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    new_id = max([task["id"] for task in tasks], default=0) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)
    with open("database", "w") as f:
        json.dump(tasks, f, indent=4)

    return new_task