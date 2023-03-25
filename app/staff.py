from fastapi import FastAPI, APIRouter,Request
import pymongo
from bson import ObjectId
import json
import time

app = FastAPI()
router = APIRouter()

client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

# save staff 
@router.post("/")
async def saveStaff(request:Request):
    try:
        body = await request.json()
        body['password'] = str(int(time.time()))[-6:]
        body['created_at'] = int(time.time())
        db['staff'].insert_one(body)
        return {"status" : True ,"message" : "Staff added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}
    
# get all staff
@router.get("/")
async def getstaff():
    try:
        staff = list(db['staff'].find())
        return {"status" : True ,"message" : "staff found" ,"data":json.loads(json.dumps(staff,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}
    
# get Staff by id
@router.get("/{id}")
async def getStaff(id):
    try:
        Staff = db['staff'].find_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Staff found" ,"data":json.loads(json.dumps(Staff,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# update Staff
@router.post("/update/{id}")
async def updateStaff(id,request:Request):
    try:
        body = await request.json()
        db['staff'].update_one({"_id":ObjectId(id)},{'$set':body})
        return {"status" : True ,"message" : "Staff updated" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# delete Staff
@router.post("/delete/{id}")
async def deleteStaff(id):
    try:
        db['staff'].delete_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Staff deleted" }
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# Staff login
@router.post("/login")
async def login(request:Request):
    try:
        body = await request.json()
        Staff = db['staff'].find_one({"phone_number":body['email'],"password":body['password']})
        if Staff:
            return {"status" : True ,"message" : "Staff found" ,"data":json.loads(json.dumps(Staff,default=str)),"type":"staff"}
        else:
            return {"status" : False ,"message" : "Wrong phone number or password" }
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# get staff attendance
@router.get("/attendance1")
async def getAttendance():
    try:
        attendance = list(db['staff'].find())
        return {"status" : True ,"message" : "Attendance found" ,"data":json.loads(json.dumps(attendance,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong","data":str(e)}

# staff attendance
@router.post("/attendance")
async def attendance(request:Request):
    try:
        body = await request.json()
        check = db['staff_attendance'].find_one({"staff_id":ObjectId(body['staff_id']),"date":body['date']})
        if check:
            return {"status" : False ,"message" : "Attendance already added" }
        body['date'] = body['date']
        body['staff_id'] = ObjectId(body['staff_id'])
        body['created_at'] = int(time.time())
        db['staff_attendance'].insert_one(body)
        return {"status" : True ,"message" : "Attendance added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

