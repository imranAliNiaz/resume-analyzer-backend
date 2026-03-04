from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import agents.resume_analysis_agent as agent
from controllers import auth_controller, resume_analysis_controller

router = agent.agentic_job_search_router
security = HTTPBearer()


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Unified analysis endpoint:
    Delegates logic to resume_analysis_controller.py
    """
    try:
        user = await auth_controller.get_current_user_from_token(
            credentials.credentials
        )
        result = await resume_analysis_controller.analyze_resume_controller(
            file, job_description, user
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/history")
async def get_history(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Retrieve all past analyses for the logged-in user"""
    try:
        user = await auth_controller.get_current_user_from_token(
            credentials.credentials
        )
        history = await resume_analysis_controller.get_history_controller(user["id"])
        return JSONResponse(history)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/history/{analysis_id}")
async def get_single_analysis(
    analysis_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Retrieve a specific analysis by ID"""
    try:
        user = await auth_controller.get_current_user_from_token(
            credentials.credentials
        )
        analysis_record = (
            await resume_analysis_controller.get_single_analysis_controller(
                analysis_id, user["id"]
            )
        )
        return JSONResponse(analysis_record)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/rag/{user_id}")
async def upload_only(user_id: str, file: UploadFile = File(...)):
    """Keep for simple uploads without immediate analysis"""
    try:
        result = await resume_analysis_controller.upload_only_controller(file)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
