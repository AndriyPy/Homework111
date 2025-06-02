from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
import uvicorn
import sqlite3
from datetime import datetime


def init_db():
    connection = sqlite3.connect('netflix.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Movie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            director TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            rating FLOAT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()

app = FastAPI(on_startup=[init_db])

class Movie(BaseModel):
    title: str = Field(..., description="Title of the movie")
    director: str = Field(..., description="Name of the movie's director")
    release_year: int = Field(..., description="Year the movie was released")
    rating: float = Field(..., ge=0, le=10, description="Rating of the movie (from 0 to 10)")


@app.get("/movies", status_code=200)
async def get_movies():
    conn = None
    try:
        conn = sqlite3.connect('netflix.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Movie')
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No movies found")
        return rows

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=404, detail=f"Database error: {e}")

    finally:
        if conn is not None:
            conn.close()

@app.post("/movies", status_code=201)
async def add_movie(movie:Movie):
    conn = None
    try:
        conn = sqlite3.connect('netflix.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''SELECT id FROM Movie WHERE title = ?''',(movie.title,))
        existing_movie = cursor.fetchone()

        if existing_movie:
            raise HTTPException(status_code=400,detail=f"Task with title '{movie.title}' already exists")

        if movie.release_year > datetime.now().year:
            raise HTTPException(status_code=400, detail="Release year cannot be in the future")

        cursor.execute(
            '''INSERT INTO Movie (title, director, release_year, rating) VALUES (?, ?, ?, ?)''',
            (movie.title, movie.director, movie.release_year, movie.rating)
        )
        conn.commit()
        return {"message": f"Movie '{movie.title}' was added"}

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()

@app.get("/movies/{id}")
async def get_movie(id: int):
    conn = None
    try:
        conn = sqlite3.connect('netflix.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM Movie WHERE id = ?', (id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Movie not found")

        return row
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()

@app.delete("/movies/{id}")
async def delete_movie(id:int):
    conn = None
    try:
        conn = sqlite3.connect('netflix.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()


        cursor.execute('SELECT * FROM Movie WHERE id = ?', (id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Movie not found")

        cursor.execute('DELETE FROM Movie WHERE id = ?', (id,))
        conn.commit()
        return {"message": f"Movie '{row['title']}' was deleted"}

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()



if __name__ == "__main__":
    uvicorn.run("netflixhomework:app", reload=True)