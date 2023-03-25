from fastapi import FastAPI, APIRouter,Request,Response
import pymongo
from bson import ObjectId
import json
import time

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from typing import List

app = FastAPI()
router = APIRouter()

client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

#generate roll number function
def generate_roll_number(class_id):
    students = list(db['students'].find({"class_id":class_id}))
    if students:
        roll_number = students[-1]['roll_number'] + 1
    else:
        roll_number = 1
    return roll_number

@router.get("/fees_report")
async def feesReport(response: Response):
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
                    'as': 'class'
                }
            }, {
                '$project': {
                    'student_id': '$_id', 
                    'name': {
                        '$arrayElemAt': [
                            '$result.first_name', 0
                        ]
                    }, 
                    'amount': 1,
                    'class': {
                        '$arrayElemAt': [
                            '$class.name', 0
                        ]
                    },
                    "created_at": 1
                }
            }
        ]))
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = 'attachment; filename="report.pdf"'

        doc = SimpleDocTemplate(response.body, pagesize=letter)
        styles = getSampleStyleSheet()
        data = fees
        data_table = Table([list(data[0].keys())] + [[d[k] for k in d] for d in data])
        print("data_table",data_table)
        # Add table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])
        data_table.setStyle(table_style)

        # Build the PDF document
        elements = []
        elements.append(data_table)
        doc.build(elements)
        return response
        # return {"status" : True ,"message" : "Fees report found" ,"data":json.loads(json.dumps(fees,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get all student marks (first_name,last_name,class_name,exam name,average obtained marks, total marks)
@router.get("/marks")
async def getMarks(request:Request):
    try:
        query = {}
        # check student_id is present in query string 
        if request.query_params.get('student_id') != "":
            query['student_id'] = ObjectId(request.query_params.get('student_id'))
        marks = list(db['student_marks'].aggregate([
            {
                '$match': query
            },
            {
                '$lookup': {
                    'from': 'students', 
                    'localField': 'student_id', 
                    'foreignField': '_id', 
                    'as': 'student'
                }
            }, {
                '$lookup': {
                    'from': 'class', 
                    'localField': 'class_id', 
                    'foreignField': '_id', 
                    'as': 'class'
                }
            }, {
                '$lookup': {
                    'from': 'exam', 
                    'localField': 'exam_id', 
                    'foreignField': '_id', 
                    'as': 'exam'
                }
            }, {
                '$project': {
                    'name': {
                        '$arrayElemAt': [
                            '$student.first_name', 0
                        ]
                    }, 
                    'middle_name': {
                        '$arrayElemAt': [
                            '$student.middle_name', 0
                        ]
                    }, 
                    'last_name': {
                        '$arrayElemAt': [
                            '$student.last_name', 0
                        ]
                    }, 
                    'exam': {
                        '$arrayElemAt': [
                            '$exam.name', 0
                        ]
                    }, 
                    'class': {
                        '$arrayElemAt': [
                            '$class.name', 0
                        ]
                    }, 
                    'obtained_mark': {
                        '$sum': '$marks.obtained_mark'
                    }, 
                    'out_of': {
                        '$sum': '$marks.out_of'
                    }
                }
            }
        ]))
        return {"status" : True ,"message" : "Marks found" ,"data":json.loads(json.dumps(marks,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save student 
@router.post("/")
async def saveStudent(request:Request):
    try:
        body = await request.json()
        #generate 6 digit password
        body['class_id'] = ObjectId(body['class_id'])
        body['password'] = str(int(time.time()))[-6:]
        body['roll_number'] = generate_roll_number(body['class_id'])
        body['created_at'] = int(time.time())
        db['students'].insert_one(body)
        return {"status" : True ,"message" : "Student added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}
    
# get all students
@router.get("/")
async def getStudents():
    try:
        students = list(db['students'].aggregate([
                {
                    '$lookup': {
                        'from': 'class', 
                        'localField': 'class_id', 
                        'foreignField': '_id', 
                        'as': 'result'
                    }
                }, {
                    '$project': {
                        'first_name': 1, 
                        'middle_name': 1, 
                        'last_name': 1, 
                        'class': {
                            '$arrayElemAt': [
                                '$result.name', 0
                            ]
                        }, 
                        'parent_number': 1, 
                        'dob': 1, 
                        'gender': 1, 
                        'address': 1, 
                        'roll_number': 1
                    }
                }
            ]))
        return {"status" : True ,"message" : "Students found" ,"data":json.loads(json.dumps(students,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}
    
# get student by id
@router.get("/{id}")
async def getStudent(id):
    try:
        student = db['students'].find_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Student found" ,"data":json.loads(json.dumps(student,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

#get student by class
@router.get("/class/{id}")
def getStudentByClass(id):
    try:
        student = list(db['students'].find({"class_id":ObjectId(id)}))
        return {"status" : True ,"message" : "Student found" ,"data":json.loads(json.dumps(student,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# update student
@router.post("/update/{id}")
async def updateStudent(id,request:Request):
    try:
        body = await request.json()
        db['students'].update_one({"_id":ObjectId(id)},{'$set':body})
        return {"status" : True ,"message" : "Student updated" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# delete student
@router.post("/delete/{id}")
async def deleteStudent(id):
    try:
        db['students'].delete_one({"_id":ObjectId(id)})
        return {"status" : True ,"message" : "Student deleted" }
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# student login
@router.post("/login")
async def login(request:Request):
    try:
        body = await request.json()
        student = db['students'].find_one({"roll_number":body['roll_no'],"class_id":ObjectId(body['class_id']),"password":body['password']})
        if student:
            return {"status" : True ,"message" : "Student found" ,"data":json.loads(json.dumps(student,default=str)),"type":"student"}
        else:
            return {"status" : False ,"message" : "Wrong roll number or password" }
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

# student attendance 
@router.post("/attendance")
async def attendance(request:Request):
    try:
        body = await request.json()
        get = db['student_attendance'].find_one({"date":body['date'],"class_id":ObjectId(body['class_id'])})
        if get:
            # update attendance
            for i in body['attendance']:
                i['student_id'] = ObjectId(i['student_id'])
            body['class_id'] = ObjectId(body['class_id'])
            db['student_attendance'].update_one({"_id":get['_id']},{'$set':body})
            return {"status" : True ,"message" : "Attendance updated" }
        for i in body['attendance']:
            i['student_id'] = ObjectId(i['student_id'])
        body['class_id'] = ObjectId(body['class_id'])
        body['created_at'] = int(time.time())
        db['student_attendance'].insert_one(body)
        return {"status" : True ,"message" : "Attendance added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

#get specific student attendance
@router.get("/attendance/{student_id}")
async def getAttendance(student_id):
    try:
        attendance = list(db['student_attendance'].aggregate([
            {
                '$unwind': {
                    'path': '$attendance'
                }
            }, {
                '$match': {
                    'attendance.student_id': ObjectId(student_id)
                }
            }, {
                '$project': {
                    'date': 1, 
                    'class_id': 1, 
                    'student_id': '$attendance.student_id', 
                    'status': '$attendance.status'
                }
            }, {
                '$lookup': {
                    'from': 'class', 
                    'localField': 'class_id', 
                    'foreignField': '_id', 
                    'as': 'result'
                }
            }, {
                '$lookup': {
                    'from': 'students', 
                    'localField': 'student_id', 
                    'foreignField': '_id', 
                    'as': 'student_result'
                }
            }, {
                '$project': {
                    'status': 1, 
                    'class': {
                        '$arrayElemAt': [
                            '$result.name', 0
                        ]
                    }, 
                    'name': {
                        '$concat': [
                            {
                                '$arrayElemAt': [
                                    '$student_result.first_name', 0
                                ]
                            }, ' ', {
                                '$arrayElemAt': [
                                    '$student_result.last_name', 0
                                ]
                            }
                        ]
                    }, 
                    'date': 1
                }
            }
        ]))
        return {"status" : True ,"message" : "Attendance found" ,"data":json.loads(json.dumps(attendance,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get student attendance
@router.get("/attendance/{date}/{class_id}")
async def getAttendance(date,class_id):
    try:
        attendance = list(db['student_attendance'].aggregate([
                {
                    '$match': {
                        'date': date,
                        'class_id': ObjectId(class_id)
                    }
                },
                {
                    '$unwind': {
                        'path': '$attendance'
                    }
                }, {
                    '$lookup': {
                        'from': 'students', 
                        'localField': 'attendance.student_id', 
                        'foreignField': '_id', 
                        'as': 'result'
                    }
                }, {
                    '$group': {
                        '_id': '$_id', 
                        'attendance': {
                            '$push': {
                                'student_id': '$attendance.student_id', 
                                'name': {
                                    '$arrayElemAt': [
                                        '$result.first_name', 0
                                    ]
                                }, 
                                'status': '$attendance.status'
                            }
                        }
                    }
                }
            ]))
        if len(attendance) > 0:
            return {"status" : True ,"message" : "Attendance found" ,"data":json.loads(json.dumps(attendance[0],default=str))}
        else:
            attendance = list(db['students'].aggregate([
                    {
                        '$group': {
                            '_id': '$class_id', 
                            'attendance': {
                                '$push': {
                                    'student_id': '$_id', 
                                    'name': '$first_name', 
                                    'status': 'present'
                                }
                            }
                        }
                    }
                ]))
            return {"status" : True ,"message" : "Attendance found","data":json.loads(json.dumps(attendance[0],default=str)) }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save fees of student
@router.post("/fees")
async def fees(request:Request):
    try:
        body = await request.json()
        body['student_id'] = ObjectId(body['student_id'])
        body['class_id'] = ObjectId(body['class_id'])
        body['created_at'] = int(time.time())
        db['student_fees'].insert_one(body)
        return {"status" : True ,"message" : "Fees added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"} 

# get student fees
@router.get("/fees/{class_id}/{student_id}")
async def getFees(class_id,student_id):
    try:
        fees_structure = db['fees_structure'].find_one({"class_id":ObjectId(class_id)})
        fees = list(db['student_fees'].find({"class_id":ObjectId(class_id),"student_id":ObjectId(student_id)}))

        # calculate total fees
        total_fees = 0
        for i in fees:
            total_fees += i['amount']
        # calculate pending fees
        pending_fees = fees_structure['amount'] - total_fees
        if pending_fees <= 0:
            return {"status" : False ,"message" : "Fees completed done" ,"data":pending_fees}
        else:
            return {"status" : True ,"message" : "Fees remaining" ,"data":pending_fees}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get student fees history (name , class name,amount , date,)
@router.get("/fees_history/{student_id}")
async def getFeesHistory(student_id):
    try:
        fees = list(db['student_fees'].aggregate([
                {
                    '$match': {
                        'student_id': ObjectId(student_id)
                    }
                }, {
                    '$lookup': {
                        'from': 'students', 
                        'localField': 'student_id', 
                        'foreignField': '_id', 
                        'as': 'result'
                    }
                }, {
                    '$lookup': {
                        'from': 'classes', 
                        'localField': 'class_id', 
                        'foreignField': '_id', 
                        'as': 'class'
                    }
                }, {
                    '$project': {
                        '_id': 0, 
                        'student_id': 1, 
                        'class_id': 1, 
                        'amount': 1, 
                        'created_at': 1, 
                        'name': {
                            '$arrayElemAt': [
                                '$result.first_name', 0
                            ]
                        }, 
                        'class_name': {
                            '$arrayElemAt': [
                                '$class.name', 0
                            ]
                        }
                    }
                }
            ]))
        if len(fees) > 0:
            return {"status" : True ,"message" : "Fees history found" ,"data":json.loads(json.dumps(fees,default=str))}
        else:
            return {"status" : False ,"message" : "Fees history not found" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# save student marks
@router.post("/marks")
async def marks(request:Request):
    try:
        body = await request.json()
        check = db['student_marks'].find_one({"class_id":ObjectId(body['class_id']),"student_id":ObjectId(body['student_id']),"exam_id":ObjectId(body['exam_id'])})
        if check:
            return {"status" : False ,"message" : "Marks already added" }
        body['student_id'] = ObjectId(body['student_id'])
        body['class_id'] = ObjectId(body['class_id'])
        body['exam_id'] = ObjectId(body['exam_id'])
        for i in body['marks']:
            i['subject_id'] = ObjectId(i['subject_id'])
        body['created_at'] = int(time.time())
        db['student_marks'].insert_one(body)
        return {"status" : True ,"message" : "Marks added" }
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

# get student marks
@router.get("/marks/{student_id}")
def getMarks(student_id):
    try:
        marks = list(db['student_marks'].aggregate([
            {
                '$match': {
                    'student_id': ObjectId(student_id)
                }
            },
            {
                '$lookup': {
                    'from': 'students', 
                    'localField': 'student_id', 
                    'foreignField': '_id', 
                    'as': 'student'
                }
            }, {
                '$lookup': {
                    'from': 'class', 
                    'localField': 'class_id', 
                    'foreignField': '_id', 
                    'as': 'class'
                }
            }, {
                '$lookup': {
                    'from': 'exam', 
                    'localField': 'exam_id', 
                    'foreignField': '_id', 
                    'as': 'exam'
                }
            }, {
                '$project': {
                    'name': {
                        '$arrayElemAt': [
                            '$student.first_name', 0
                        ]
                    }, 
                    'middle_name': {
                        '$arrayElemAt': [
                            '$student.middle_name', 0
                        ]
                    }, 
                    'last_name': {
                        '$arrayElemAt': [
                            '$student.last_name', 0
                        ]
                    }, 
                    'exam': {
                        '$arrayElemAt': [
                            '$exam.name', 0
                        ]
                    }, 
                    'class': {
                        '$arrayElemAt': [
                            '$class.name', 0
                        ]
                    }, 
                    'obtained_mark': {
                        '$sum': '$marks.obtained_mark'
                    }, 
                    'out_of': {
                        '$sum': '$marks.out_of'
                    }
                }
            }
        ]))
        return {"status" : True ,"message" : "Marks found" ,"data":json.loads(json.dumps(marks,default=str))}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}


