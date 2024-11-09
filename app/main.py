from fastapi import FastAPI, Response,status, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from random import randrange
import psycopg
from psycopg.rows import dict_row
import time
from sqlalchemy.orm import Session
from . import models
from .database import engine, SessionLocal

models.Base.metadat.create_all(bind=engine)

app = FastAPI()

# dependecy
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# model 정의
class Post(BaseModel):
    title: str
    content: str
    published: bool = True # default 값
    # rating: Optional[int] = None # optional 타입, 기본 none

while True:
    try:
        conn = psycopg.connect(host='localhost', dbname='fastapi', user='postgres', password='0404', row_factory=dict_row)
        cursor = conn.cursor()
        print("Database connected successfully")
        break
    except Exception as error:
        print("Connecting to database failed")
        print("Error: ", error)
        time.sleep(2)

# model 저장할 global array 정의
# my_posts = [{"title": "title 1", "content": "content 1", "id": 1}, {"title": "title 2", "content": "content 2", "id": 2}]

# def find_post(id):
#     for p in my_posts:
#         if p["id"] == id:
#             return p
        
# def find_index_post(id):
#     for i, p in enumerate(my_posts):
#         if p["id"] == id:
#             return i

# 순서 의미 있음 - 주소 + crud 메소드 일치하는 것 발견하면 바로 리턴
@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
    return {"status": "success"}

@app.get("/posts")
def get_posts():
    cursor.execute("""select * from posts""")
    posts = cursor.fetchall()
    return {"data": posts} # array return하면 자동으로 json으로 serialize해줌

@app.post("/posts", status_code=status.HTTP_201_CREATED) # crud naming convention: [모델 + s] 로만 한정  # default status code 설정 가능
def create_post(post: Post): # front에서 특정 모델로 데이터 받아오도록

    # post_dict = post.model_dump() # post는 basemodel 타입으로, model 데이터를 dict로 변환, 추후 사용 가능
    # post_dict['id'] = randrange(0, 10000)
    # my_posts.append(post_dict)

    cursor.execute("""insert into posts (title, content, published) values (%s, %s, %s) returning *""", (post.title, post.content, post.published)) # sql injection 방지위해 f-sring 사용 안함
    new_post = cursor.fetchone()
    conn.commit() # 변경사항 저장해야함

    return {"data": new_post}

@app.get("/posts/{id}") # path parameter 사용 (str임)
def get_post(id: int): # int임을 지정하고, int만 받아오도록

    cursor.execute("""select * from posts where id = %s""", (str(id),)) # id 다시 str로 변환
    post = cursor.fetchone()

    # post = find_post(id)

    if not post:
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"message": f"post with id: {id} was not found"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    
    return {"post_detail": post}

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):

    cursor.execute("""delete from posts where id = %s returning *""", (str(id),))
    deleted_post = cursor.fetchone()

    # index = find_index_post(id)

    if deleted_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")
    
    # my_posts.pop(index)
    conn.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    
    cursor.execute("""update posts set title = %s, content = %s, published = %s where id = %s returning *""", (post.title, post.content, post.published, str(id),))
    updated_post = cursor.fetchone()

    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")
    
    conn.commit()

    # post_dict = post.model_dump()
    # post_dict['id'] = id
    # my_posts[index] = post_dict
    return {"data": updated_post}