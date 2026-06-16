from fastapi import FastAPI
import datetime

app = FastAPI()

alerts = []

@app.get("/alerts")
def get_alerts():
    return {"alerts": alerts}

@app.post("/alerts")
def add_alert(ear: float):
    alert = {
        "timestamp": str(datetime.datetime.now()),
        "ear": ear
    }
    alerts.append(alert)
    return {"message": "Alert saved", "alert": alert}