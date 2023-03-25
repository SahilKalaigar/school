from fastapi import FastAPI, APIRouter,Request
import pymongo
from bson import ObjectId
import json
import time

app = FastAPI()
router = APIRouter()

client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

#all crud operations  of subject
@router.get("/")
async def get():
    try:
        subject = list(db['class'].find())
        return {"status" : True ,"message" : "Subject found" ,"data":json.loads(json.dumps(subject,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

@router.get("/{id}")
async def get(id):
    try:
        subject = db['class'].find_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Subject found" ,"data":json.loads(json.dumps(subject,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

@router.post("/")
async def save(request:Request):
    try:
        body = await request.json()
        db['class'].insert_one(body)
        return {"status" : True ,"message" : "Subject added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

@router.post("/update/{id}")
async def update(id,request:Request):
    try:
        body = await request.json()
        db['class'].update_one({"_id":ObjectId(id)},{'$set':body})
        return {"status" : True ,"message" : "Subject updated" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

@router.post("/delete/{id}")
async def delete(id):
    try:
        db['class'].delete_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Subject deleted" }
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}