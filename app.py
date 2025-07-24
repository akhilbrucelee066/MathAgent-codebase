# import os
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from math_agent import math_agent, is_math_question, perform_web_search
import uvicorn
from fastapi.responses import JSONResponse
import json

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

agent = math_agent()

FEEDBACK_FILE = BASE_DIR / "knowledge" / "feedback.json"

def save_feedback(feedback):
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = [{"question": "blank", "answer": "blank", "feedback": "up"}]
    data.append(feedback)
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    if not is_math_question(question):
        return JSONResponse({"response": "Sorry, I can only answer mathematics-related questions. Please ask a math question!! Articulate Query correctly!!"})
    try:
        response = agent.ask_agent(question)
        if isinstance(response, dict) and response.get("permission_required"):
            return JSONResponse(response)
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"}, status_code=500)

@app.post("/web_search")
async def web_search(question: str = Form(...)):
    try:
        web_result = perform_web_search(question)
        response = agent.present_web_answer(question, web_result)
        return JSONResponse({"response": response, "source": "web"})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"}, status_code=500)

@app.post("/feedback")
async def feedback_endpoint(question: str = Form(...), answer: str = Form(...), feedback: str = Form(...)):
    save_feedback({"question": question, "answer": answer, "feedback": feedback})
    return JSONResponse({"status": "success"})

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
    
# if __name__ == "__main__":
#     BASE_DIR = Path(__file__).parent
# else:
#     # For Vercel deployment
#     BASE_DIR = Path(os.getcwd())
