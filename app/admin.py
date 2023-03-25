from fastapi import FastAPI, APIRouter,Request
import pymongo
from bson import ObjectId
import json
import time

app = FastAPI()
router = APIRouter()

client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

# admin login
@router.post("/login")
async def login(request:Request):
    try:
        body = await request.json()
        admin = db['admins'].find_one({"email":body['email'],"password":body['password']})
        if admin:
            return {"status" : True ,"message" : "Login success" ,"data":json.loads(json.dumps(admin,default=str)),"type":"admin"}
        else:
            return {"status" : False ,"message" : "Invalid credentials"}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save school details
@router.post("/school")
async def saveSchool(request:Request):
    try:
        body = await request.json()
        body['created_at'] = int(time.time())
        db['school'].insert_one(body)
        return {"status" : True ,"message" : "School details added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save exams
@router.post("/exam")
async def saveExam(request:Request):
    try:
        body = await request.json()
        body['created_at'] = int(time.time())
        db['exam'].insert_one(body)
        return {"status" : True ,"message" : "Exam added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get all exams
@router.get("/exam")
async def getExam():
    try:
        exam = list(db['exam'].find())
        return {"status" : True ,"message" : "Exam found" ,"data":json.loads(json.dumps(exam,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# update exam
@router.post("/exam/update/{id}")
async def updateExam(id,request:Request):
    try:
        body = await request.json()
        db['exam'].update_one({"_id":ObjectId(id)},{'$set':body})
        return {"status" : True ,"message" : "Exam updated" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# delete exam
@router.post("/exam/delete/{id}")
async def deleteExam(id):
    try:
        db['exam'].delete_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Exam deleted" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save fees structure
@router.post("/fees")
async def saveFees(request:Request):
    try:
        body = await request.json()
        body['class_id'] = ObjectId(body['class_id'])
        body['created_at'] = int(time.time())
        db['fees_structure'].insert_one(body)
        return {"status" : True ,"message" : "Fees structure added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get all fees structure
@router.get("/fees")
async def getFees():
    try:
        fees = list(db['fees_structure'].aggregate([
                    {
                        '$lookup': {
                            'from': 'class', 
                            'localField': 'class_id', 
                            'foreignField': '_id', 
                            'as': 'result'
                        }
                    }, {
                        '$project': {
                            'class_id': 1, 
                            'amount': 1, 
                            'name': {
                                '$arrayElemAt': [
                                    '$result.name', 0
                                ]
                            }
                        }
                    }
                ]))
        return {"status" : True ,"message" : "Fees structure found" ,"data":json.loads(json.dumps(fees,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# update fees structure
@router.put("/fees/{id}")
async def updateFees(id,request:Request):
    try:
        body = await request.json()
        db['fees_structure'].update_one({"_id":ObjectId(id)},{'$set':body})
        return {"status" : True ,"message" : "Fees structure updated" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save expenses
@router.post("/expenses")
async def saveExpenses(request:Request):
    try:
        body = await request.json()
        body['created_at'] = int(time.time())
        db['expenses'].insert_one(body)
        return {"status" : True ,"message" : "Expenses added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get all expenses
@router.get("/expenses")
async def getExpenses():
    try:
        expenses = list(db['expenses'].find())
        return {"status" : True ,"message" : "Expenses found" ,"data":json.loads(json.dumps(expenses,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# get remaining amount add all student fees and subtract expenses
@router.get("/balance")
async def getRemaining():
    try:
        fees = list(db['fees_structure'].aggregate([
                    {
                        '$group': {
                            '_id': None, 
                            'amount': {
                                '$sum': '$amount'
                            }
                        }
                    }
                ]))
        expenses = list(db['expenses'].aggregate([
                    {
                        '$group': {
                            '_id': None, 
                            'amount': {
                                '$sum': '$amount'
                            }
                        }
                    }
                ]))
        total_fees = fees[0]['amount'] if fees else 0
        total_expenses = expenses[0]['amount'] if expenses else 0
        remaining = total_fees - total_expenses
        return {"status" : True ,"message" : "Remaining amount found" ,"data":remaining}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

