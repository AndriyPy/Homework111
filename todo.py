from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sqlite3



class Task(BaseModel):
    title: str
    description: str

class EditTask(BaseModel):
    id: int
    title: str
    description: str

class DeleteTask(BaseModel):
    id: int


def init_db():
    connection = sqlite3.connect('todo.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Todolist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()

app = FastAPI(on_startup=[init_db])

@app.post('/createtask/')
async def create_task(task: Task):
    connection = None
    try:
        connection = sqlite3.connect('todo.db')
        cursor = connection.cursor()

        cursor.execute('''SELECT id FROM Todolist WHERE title = ?''',(task.title,))
        existing_task = cursor.fetchone()

        if existing_task:
            raise HTTPException(status_code=400,detail=f"Task with title '{task.title}' already exists")

        cursor.execute(
            '''INSERT INTO Todolist (title, description) VALUES (?, ?)''',
            (task.title, task.description)
        )
        connection.commit()
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if connection is not None:
            connection.close()

    return {"message": f"Task '{task.title}' added"}


@app.put('/edit_task/')
async def edit_task(task: EditTask):
    conn = None
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Todolist WHERE id = ?', (task.id,))
        tas = cursor.fetchone()

        if not tas:
            raise HTTPException(status_code=404, detail="Task not found")
        cursor.execute('UPDATE Todolist SET title = ?, description = ? WHERE id = ?',(task.title, task.description, task.id))
        conn.commit()
        return {"message": f"Task '{task.title}' updated"}


    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if conn is not None:
            conn.close()


@app.delete('/deletetask/')
async def delete_task(task:DeleteTask):
    conn = None
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Todolist WHERE id = ?', (task.id,))
        one = cursor.fetchone()

        if not one:
            raise HTTPException(status_code=404, detail="Task not found")

        cursor.execute('DELETE FROM Todolist WHERE id = ?', (task.id,))
        conn.commit()
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


    finally:
        if conn is not None:
            conn.close()
    return {"message": f"Task with id {task.id} deleted"}


@app.get('/one_task/')
async def one_task(id: int):
    conn = None
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Todolist WHERE id = ?', (id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "id": row[0],
            "title": row[1],
            "description": row[2]
        }


    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if conn is not None:
            conn.close()


@app.get('/tasks/')
async def get_tasks():
    conn = None
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Todolist')
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No tasks found")

        tasks = []

        for row in rows:
            task = {
                "id": row[0],
                "title": row[1],
                "description": row[2]
            }
            tasks.append(task)

        return {"tasks": tasks}


    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=404, detail=f"Database error: {e}")


    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    uvicorn.run("todo:app", reload=True)