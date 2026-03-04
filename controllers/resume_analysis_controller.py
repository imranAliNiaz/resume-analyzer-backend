from fastapi import UploadFile, HTTPException
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.messages import HumanMessage
import agents.resume_analysis_agent as agent
from controllers import auth_controller, history_controller


async def analyze_resume_controller(file: UploadFile, job_description: str, user: dict):
    """
    Unified analysis controller:
    - Parses, indexes, and runs agentic analysis
    - Saves result to history
    """
    print(f"\n[CONTROLLER] Processing analysis for: {file.filename}")

    try:
        suffix = os.path.splitext(file.filename)[1].lower()
        if suffix not in [".pdf", ".docx", ".txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {suffix}. Supported: .pdf, .docx, .txt",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 1. Parse and Index
            if suffix == ".pdf":
                loader = PyPDFLoader(tmp_path)
            elif suffix == ".docx":
                loader = Docx2txtLoader(tmp_path)
            else:
                loader = TextLoader(tmp_path)

            docs = loader.load()
            agent.job_find_rag(docs)

            user_id = user["id"]
            graph = agent.compiled_graph
            result = graph.invoke(
                {
                    "messages": [
                        HumanMessage(
                            content=f"Analyze my resume for this target role: {job_description}"
                        )
                    ]
                }
            )

            analysis = result.get("analysis_result")
            if not analysis:
                raise HTTPException(
                    status_code=500, detail="Failed to generate analysis result."
                )

            analysis_dict = analysis.model_dump()
            await history_controller.save_analysis(
                user_id, job_description, analysis_dict
            )

            return analysis_dict

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        print(f"❌ Controller Analysis Error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


async def get_history_controller(user_id: str):
    """Retrieve all past analyses for a user"""
    try:
        return await history_controller.get_user_history(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_single_analysis_controller(analysis_id: str, user_id: str):
    """Retrieve a specific analysis after ownership verification"""
    try:
        analysis_record = await history_controller.get_analysis_by_id(analysis_id)
        if analysis_record["user_id"] != user_id:
            raise HTTPException(
                status_code=403, detail="Unauthorized access to this report"
            )
        return analysis_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def upload_only_controller(file: UploadFile):
    """Simple upload and indexing without analysis"""
    try:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                loader = PyPDFLoader(tmp_path)
            elif suffix == ".docx":
                loader = Docx2txtLoader(tmp_path)
            else:
                loader = TextLoader(tmp_path)

            agent.job_find_rag(loader.load())
            return {"message": "Resume uploaded and indexed ✅"}
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
