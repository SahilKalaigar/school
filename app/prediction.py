from fastapi import FastAPI, APIRouter,Request,Response
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
app = FastAPI()
router = APIRouter()

@router.post("/")
async def get(request:Request):
    try:
        # df = pd.read_csv('data.csv')
        # X = df.iloc[:, :-1].values
        # y = df.iloc[:, 1].values
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
        # regressor = LinearRegression()
        # regressor.fit(X_train, y_train)
        # y_pred = regressor.predict(X_test)
        body = await request.json()
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
        predict = reg.predict([[body['current_mark'],body['attendance'] ,body['extra_activities'] ]])
        predict = int(list(predict)[0])

        return {"status" : True ,"message" : "Prediction found" ,"data":json.loads(json.dumps(predict,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : "Something wrong"}