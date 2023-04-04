from fastapi import FastAPI, APIRouter,Request
import pymongo
from bson import ObjectId
import json
import time
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import base64

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
        check = db['fees_structure'].find_one({"class_id":ObjectId(body['class_id'])})
        if check:
            return {"status" : False ,"message" : "Fees structure already added for this class" }
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
                    }, 
                    {
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

# get student paid fees (student name , class name , paid amount)
@router.get("/fees/paid")
async def getFeesPaid():
    try:
        fees = list(db['student_fees'].aggregate([
                    {
                        '$lookup': {
                            'from': 'students', 
                            'localField': 'student_id', 
                            'foreignField': '_id', 
                            'as': 'result'
                        }
                    },  
                    {
                        '$lookup': {
                            'from': 'class', 
                            'localField': 'class_id', 
                            'foreignField': '_id', 
                            'as': 'class_result'
                        }
                    }, 
                    {
                        '$project': {
                            'student_id': 1, 
                            'amount': 1, 
                            'name': {'$concat': [{'$arrayElemAt': ['$result.first_name', 0]}, ' ', {'$arrayElemAt': ['$result.last_name', 0]}]},
                            'class_id': 1,
                            'class_name': {
                                '$arrayElemAt': [
                                    '$class_result.name', 0
                                ]
                            },
                            'created_at':{
                                '$toDate': {
                                '$multiply': [
                                    { '$toLong': "$created_at" },
                                    1000
                                ]
                                }
                            },
                            'category':1
                        }
                    }
                ]))
        return {"status" : True ,"message" : "Fees paid found" ,"data":json.loads(json.dumps(fees,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# update fees structure
@router.post("/fees/update/{id}")
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
        fees = list(db['student_fees'].aggregate([
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
        return {"status" : True ,"message" : "Remaining amount found" ,"data":remaining,"total_collected":total_fees,"total_expenses":total_expenses}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# student mark report bar chart (subject name , class name , mark)
@router.get("/mark/report")
async def getMarkReport(request:Request):
    try:
        query = {}
        # check student_id is present in query string 
        if request.query_params.get('class_id') != "":
            query['class_id'] = ObjectId(request.query_params.get('class_id'))
        get = list(db['student_marks'].aggregate([
            {
                '$match':query
            },
            {
                '$unwind': {
                    'path': '$marks'
                }
            }, {
                '$lookup': {
                    'from': 'subjects', 
                    'localField': 'marks.subject_id', 
                    'foreignField': '_id', 
                    'as': 'result'
                }
            }, {
                '$lookup': {
                    'from': 'class', 
                    'localField': 'class_id', 
                    'foreignField': '_id', 
                    'as': 'class_result'
                }
            }, {
                '$project': {
                    'class_id': 1, 
                    'exam_id': 1, 
                    'marks': 1, 
                    'subject_name': {
                        '$arrayElemAt': [
                            '$result.name', 0
                        ]
                    }, 
                    'created_at': {
                        '$toDate': {
                            '$multiply': [
                                {
                                    '$toLong': '$created_at'
                                }, 1000
                            ]
                        }
                    }, 
                    'class_name': {
                        '$arrayElemAt': [
                            '$class_result.name', 0
                        ]
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'class_name': '$class_name', 
                        'subject_name': '$subject_name'
                    }, 
                    'marks': {
                        '$avg': '$marks.obtained_mark'
                    }
                }
            }, {
                '$project': {
                    'class_name': '$_id.class_name', 
                    'subject_name': '$_id.subject_name', 
                    'marks': 1,
                    '_id': 0
                }
            }
        ]))
        if not get:
            return {"status" : False ,"message" : "Data not found" ,"data":""}
        matplotlib.pyplot.switch_backend('Agg')
        df = pd.DataFrame(get)

        # Reshape the data using pivot
        df_pivot = df.pivot(index="class_name", columns="subject_name", values="marks")

        # Create a bar chart
        df_pivot.plot(kind="bar")
        plt.xlabel("Class")
        plt.ylabel("Marks")
        plt.title("Marks by Subject and Class")
        plt.show()
        # Save the chart to a file
        plt.savefig('./images/class_wise_chart.png')

        # return base64String of bar chart
        return {"status" : True ,"message" : "Mark report found" ,"data":base64.b64encode(open('./images/class_wise_chart.png', 'rb').read()).decode('utf-8')}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# create notice board
@router.post("/notice")
async def createNotice(request:Request):
    try:
        body = await request.json()
        body['created_at'] = int(time.time())
        db['notices'].insert_one(body)
        return {"status" : True ,"message" : "Notice created" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get all notices
@router.get("/notice")
async def getNotice(request:Request):
    try:
        #convert comma seprarated string to list
        to = request.query_params.get('type').split(',')
        print(to)
        notices = list(db['notices'].find({"to":{'$in':to}}))
        return {"status" : True ,"message" : "Notice found" ,"data":json.loads(json.dumps(notices,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}