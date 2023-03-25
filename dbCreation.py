client = pymongo.MongoClient('localhost', 27017)
db = client["school"]

def create_10_class():
    try:
        db['class'].insert_many([
            {
                "name": "1st",
            },
            {
                "name": "2nd",
            },
            {
                "name": "3rd",
            },
            {
                "name": "4th",
            },
            {
                "name": "5th",
            },
            {
                "name": "6th",
            },
            {
                "name": "7th",
            },
            {
                "name": "8th",
            },
            {
                "name": "9th",
            },
            {
                "name": "10th",
            },
        ])
        print("10 class created")
    except Exception as e:
        print(e)

def create_fee_structure():
    try:
        # create fee structure for every class
        class_list = list(db['class'].find())
        for class_ in class_list:
            db['fees_structure'].insert_one({
                "class_id": class_['_id'],
                "fee": 10000 * int(class_['name'][:-2]),
                "created_at": int(time.time())
            })
        print("Fee structure created")
    except Exception as e:
        print(e)

def exams():
    try:
        db['exam'].insert_many([
            {
                "name": "Test 1",
            },
            {
                "name": "Test 2",
            },
            {
                "name": "Half Yearly",
            },
            {
                "name": "Annual",
            },
        ])
        print("Exams created")
    except Exception as e:
        print(e)

def create_subject():
    try:
        db['subject'].insert_many([
            {
                "name": "English",
            },
            {
                "name": "Hindi",
            },
            {
                "name": "Maths",
            },
            {
                "name": "Science",
            },
            {
                "name": "Social Science",
            },
        ])
        print("Subjects created")
    except Exception as e:
        print(e)

create_10_class()
create_fee_structure()
exams()
create_subject()