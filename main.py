from typing import Union
import uvicorn
from fastapi import FastAPI,Request,File,UploadFile,Form
from fastapi.staticfiles import StaticFiles
import pymongo
from bson import ObjectId
import json
import time
from fastapi.middleware.cors import CORSMiddleware
import matplotlib.pyplot as plt
import matplotlib
import base64
from app.student import router as student
from app.subject import router as subject
from app.student_class import router as classs
from app.staff import router as staff
from app.admin import router as admin
from app.prediction import router as prediction

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/files", StaticFiles(directory="files"), name="files")
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH","OPTIONS"],
    allow_headers=["*"],
)

client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

@app.get("/barchart")
def generate_barchart():
    # Data for the chart
    x = ['A', 'B', 'C', 'D', 'E']
    y = [10, 5, 8, 12, 5]
    matplotlib.pyplot.switch_backend('Agg')
    # Create the bar chart
    plt.bar(x, y)

    # Save the chart to a file
    plt.savefig('barchart.png')

    # return base64String of bar chart
    return base64.b64encode(open('barchart.png', 'rb').read()).decode('utf-8')

@app.get("/")
def read_root():
    return "Welcome to school management system"

@app.get("/attendance")
async def getAttendance():
    try:
        attendance = list(db['staff_attendance'].find())
        return {"status" : True ,"message" : "Attendance found" ,"data":json.loads(json.dumps(attendance,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong","data":str(e)}

app.include_router(student, prefix="/student", tags=["student"])
app.include_router(subject, prefix="/subject", tags=["subject"])
app.include_router(classs, prefix="/class", tags=["class"])
app.include_router(staff, prefix="/staff", tags=["staff"])
app.include_router(admin, prefix="/admin", tags=["admin"])
app.include_router(prediction, prefix="/prediction", tags=["prediction"])


if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=80, reload=True)