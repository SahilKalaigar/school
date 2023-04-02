from fastapi import FastAPI, APIRouter,Request,Response
import pymongo
from bson import ObjectId
import json
import time
import base64
import matplotlib.pyplot as plt
import matplotlib
import itertools

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

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

def getPrediction(current_mark,attendance,extra_activities):
    try:
        # Load the data into a pandas dataframe
        data = {'Current Marks': [90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0],
                'Attendance': [95, 85, 80, 90, 70, 75, 65, 70, 80, 75, 85, 80, 90, 70, 75, 65, 70, 80, 75],
                'Extra Activities': [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
                'Final Marks': [92, 87, 82, 77, 72, 68, 63, 58, 53, 49, 44, 39, 34, 29, 24, 19, 14, 9, 4]}

        df = pd.DataFrame(data)
        print(len(data['Current Marks']))
        # Split the data into training and testing sets
        X = df[['Current Marks', 'Attendance', 'Extra Activities']]
        y = df['Final Marks']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        # Train the linear regression model
        reg = LinearRegression().fit(X_train, y_train)

        # Make predictions on the test data
        y_pred = reg.predict(X_test)

        # Evaluate the model's accuracy
        # r2 = reg.score(X_test, y_test)
        # print("R2 Score:", r2)

        # check accuracy in integer 
        # print("R2 Score:", int(r2*100))

        # check prediction of given data
        # print("Prediction:", reg.predict([[90, 95, 1]]))
        # print("Prediction:", reg.predict([[45, 30, 1]]))
        predict = reg.predict([[current_mark, attendance, extra_activities ]])
        predict = int(list(predict)[0])

        return {"status" : True ,"message" : "Prediction found" ,"data":"Predicted marks is "+str(predict)+"%"}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}

def getAttendancePerformanceFun(student_id):
    try:
        performance = list(db['student_attendance'].aggregate([
            {
                '$unwind': {
                    'path': '$attendance'
                }
            }, {
                '$match': {
                    'attendance.student_id': ObjectId(student_id)
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
                    'localField': 'attendance.student_id', 
                    'foreignField': '_id', 
                    'as': 'student_result'
                }
            }, {
                '$project': {
                    'class_id': 1, 
                    'class_name': {
                        '$arrayElemAt': [
                            '$result.name', 0
                        ]
                    }, 
                    'student_name': {
                        '$arrayElemAt': [
                            '$student_result.first_name', 0
                        ]
                    }, 
                    'date': {
                        '$toDate': '$date'
                    }, 
                    'attendance': 1
                }
            }, {
                '$group': {
                    '_id': {
                        'month': {
                            '$month': '$date'
                        }, 
                        'status': '$attendance.status'
                    }, 
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$project': {
                    'month': '$_id.month', 
                    'status': '$_id.status', 
                    'count': 1, 
                    '_id': 0
                }
            }
        ]))
        if not performance:
            return {"status" : False ,"message" : "Data not found" ,"data":""}
        #avargae attendance percentage of student
        total_days = 0
        present_days = 0
        month = []
        absent = []
        present = []
        for i in performance:
            if i['status'] == 'present':
                present_days += i['count']
            total_days += i['count']
        attendance_percentage = (present_days/total_days)*100 
        # group performance array by month
        performance = sorted(performance, key=lambda k: k['month'])
        performance = [list(v) for k, v in itertools.groupby(performance, key=lambda k: k['month'])]
        # months in string
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        absent = [0] * 12  # Initialize absent list with 0 for all 12 months
        present = [0] * 12  # Initialize present list with 0 for all 12 months

        for item in performance:
            for record in item:
                if record['status'] == 'absent':
                    absent[record['month'] - 1] = record['count']
                elif record['status'] == 'present':
                    present[record['month'] - 1] = record['count']  
        matplotlib.pyplot.switch_backend('Agg')
        # df = pd.DataFrame(performance)
        
        # Plot the data
        plt.plot(months, absent, label='Absent')
        plt.plot(months, present, label='Present')

        # Set the chart title and labels
        plt.title('Absent-Present Chart')
        plt.xlabel('Month')
        plt.ylabel('Percentage')

        # Show the legend
        plt.legend()

        # Show the chart
        # plt.show()

        plt.savefig('./images/student_attendance_performance_report.png')
        return attendance_percentage
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

@router.get("/attendance")
def getAllAttendance():
    try:
        attendance = list(db['student_attendance'].aggregate([
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
                    'class_name': {
                        '$arrayElemAt': [
                            '$result.name', 0
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

# student performance report
@router.get("/performance/{student_id}/{class_id}")
def getPerformance(student_id,class_id):
    try:
        performance = list(db['student_marks'].aggregate([
            {
                '$match':{
                    'student_id':ObjectId(student_id),
                    'class_id':ObjectId(class_id)
                }
            },
            {
                '$unwind': {
                    'path': '$marks'
                }
            }, {
                '$lookup': {
                    'from': 'students', 
                    'localField': 'student_id', 
                    'foreignField': '_id', 
                    'as': 'student_result'
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
                    'from': 'exam', 
                    'localField': 'exam_id', 
                    'foreignField': '_id', 
                    'as': 'exam_result'
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
                    }, 
                    'student_name': {
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
                    'exam_name': {
                        '$arrayElemAt': [
                            '$exam_result.name', 0
                        ]
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'student_name': '$student_name'
                    }, 
                    'marks': {
                        '$push': {
                            'exam_name': '$exam_name', 
                            'subject_name': '$subject_name', 
                            'obtained_mark': '$marks.obtained_mark', 
                            'out_of': '$marks.out_of'
                        }
                    }
                }
            }
        ]))
        if not performance:
            return {"status" : False ,"message" : "Data not found" ,"data":""}
        matplotlib.pyplot.switch_backend('Agg')
        df = pd.DataFrame(performance[0]['marks'])

        # Reshape the data using pivot
        df_pivot = df.pivot(index="exam_name", columns="subject_name", values="obtained_mark")

        # Create a bar chart
        df_pivot.plot(kind="bar")
        plt.xlabel("Exam")
        plt.ylabel("Marks")
        plt.title("Marks by Subject and Exam")
        plt.show()
        # Save the chart to a file
        plt.savefig('./images/student_performance_report.png')

        attendance_percentage = getAttendancePerformanceFun(student_id)

        # Get the list of marks
        marks = performance[0]['marks']
        # Group the marks by exam_name
        grouped_marks = itertools.groupby(marks, lambda x: x['exam_name'])

        # Create a dictionary to store the grouped data
        grouped_data = {}
        total_mark = 0
        total_obtained_mark = 0
        # Loop through the grouped marks
        for exam_name, marks in grouped_marks:
            # Convert the marks iterator to a list
            marks = list(marks)
            # Add the exam_name and marks to the grouped data dictionary
            grouped_data[exam_name] = marks
            # Loop through the marks
            for mark in marks:
                # Add the mark to the total
                total_mark += mark['out_of']
                total_obtained_mark += mark['obtained_mark']
        # Calculate the average
        average = total_obtained_mark / total_mark * 100
        # call prediction function
        prediction = getPrediction(average,attendance_percentage,1)
        return {"status" : True ,"message" : "Performance found" ,"data":json.loads(json.dumps(grouped_data,default=str)),"prediction":prediction['data'],"mark":base64.b64encode(open('./images/student_performance_report.png', 'rb').read()).decode('utf-8'),"attendance":base64.b64encode(open('./images/student_attendance_performance_report.png', 'rb').read()).decode('utf-8')}
    except Exception as e:
        print(e)
        return {"status" : False ,"message" : "Something wrong"}

#student attendance performance report
@router.get("/attendance/performance/{student_id}")
def getAttendancePerformance(student_id):
    try:
        performance = list(db['student_attendance'].aggregate([
            {
                '$unwind': {
                    'path': '$attendance'
                }
            }, {
                '$match': {
                    'attendance.student_id': ObjectId(student_id)
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
                    'localField': 'attendance.student_id', 
                    'foreignField': '_id', 
                    'as': 'student_result'
                }
            }, {
                '$project': {
                    'class_id': 1, 
                    'class_name': {
                        '$arrayElemAt': [
                            '$result.name', 0
                        ]
                    }, 
                    'student_name': {
                        '$arrayElemAt': [
                            '$student_result.first_name', 0
                        ]
                    }, 
                    'date': {
                        '$toDate': '$date'
                    }, 
                    'attendance': 1
                }
            }, {
                '$group': {
                    '_id': {
                        'month': {
                            '$month': '$date'
                        }, 
                        'status': '$attendance.status'
                    }, 
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$project': {
                    'month': '$_id.month', 
                    'status': '$_id.status', 
                    'count': 1, 
                    '_id': 0
                }
            }
        ]))
        if not performance:
            return {"status" : False ,"message" : "Data not found" ,"data":""}
        #avargae attendance percentage of student
        total_days = 0
        present_days = 0
        for i in performance:
            if i['status'] == 'present':
                present_days += i['count']
            total_days += i['count']
        attendance_percentage = (present_days/total_days)*100 
        matplotlib.pyplot.switch_backend('Agg')
        df = pd.DataFrame(performance)

        # Reshape the data using pivot
        df_pivot = df.pivot(index="month", columns="status", values="count")

        # Create a bar chart
        df_pivot.plot(kind="bar")
        plt.xlabel("Month")
        plt.ylabel("Days")
        plt.title("Attendance by month")
        plt.show()
        # Save the chart to a file
        plt.savefig('./images/student_attendance_performance_report.png')
        return {"status" : True ,"message" : "Performance found" ,"data":json.loads(json.dumps(performance,default=str))}
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
                    },
                    'class_id': 1,
                    'exam_id': 1,
                    'student_id': 1
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
                        'roll_number': 1,
                        'password':1,
                        'class_id':1,
                        'date_of_admission':1,
                        'academic_year':1
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
        body['class_id'] = ObjectId(body['class_id'])
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
                                'status': '$attendance.status',
                                'created_at': {
                                    '$toDate': {
                                        '$multiply': [
                                            {
                                                '$toLong': '$created_at'
                                            }, 1000
                                        ]
                                    }
                                }
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
                        '$match': {
                            'class_id': ObjectId(class_id)
                        }
                    },
                    {
                        '$group': {
                            '_id': '$class_id', 
                            'attendance': {
                                '$push': {
                                    'student_id': '$_id', 
                                    'name': '$first_name', 
                                    'status': 'present',
                                    'created_at': date
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




