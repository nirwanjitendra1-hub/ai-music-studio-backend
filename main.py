import os
import base64
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()
app=FastAPI(title="AI Music Studio Gateway")
URL="https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL="lyria-3.5"
class GenerateRequest(BaseModel): prompt:str=Field(min_length=3,max_length=12000)
class GenerateResponse(BaseModel): audio_base64:str; mime_type:str="audio/mpeg"; lyrics:str=""
def extract(data):
    audio=None;text=[]
    for step in data.get("steps",[]):
        if step.get("type")!="model_output": continue
        for block in step.get("content",[]):
            if block.get("type")=="audio" and block.get("data"): audio=block["data"]
            if block.get("type")=="text" and block.get("text"): text.append(block["text"])
    out=data.get("output_audio") or {}
    audio=audio or out.get("data")
    if data.get("output_text"): text.append(data["output_text"])
    return audio,"\n".join(text).strip()
@app.get("/health")
async def health(): return {"ok":True,"model":MODEL}
@app.post("/generate",response_model=GenerateResponse)
async def generate(req:GenerateRequest):
    key=os.getenv("GEMINI_API_KEY")
    if not key: raise HTTPException(500,"GEMINI_API_KEY is not configured")
    prompt=f"Create an ORIGINAL song. Do not reproduce or quote any existing copyrighted song, melody, lyrics, recording, or identifiable singer voice.\n\nMusic brief:\n{req.prompt}"
    async with httpx.AsyncClient(timeout=300) as client:
        r=await client.post(URL,headers={"x-goog-api-key":key,"Content-Type":"application/json"},json={"model":MODEL,"input":prompt})
    if r.status_code>=400: raise HTTPException(r.status_code,r.text[:2000])
    audio,lyrics=extract(r.json())
    if not audio: raise HTTPException(502,"Provider returned no audio")
    try: base64.b64decode(audio,validate=True)
    except Exception: raise HTTPException(502,"Invalid audio payload")
    return GenerateResponse(audio_base64=audio,lyrics=lyrics)
