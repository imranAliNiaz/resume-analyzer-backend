from pprint import pprint
import tempfile
import time
from typing import Annotated, List, Optional
from fastapi import APIRouter
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

MODELS_TO_TRY = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
]


def get_llm(model_name: str):
    return ChatGoogleGenerativeAI(
        model=model_name, google_api_key=GOOGLE_API_KEY, temperature=0.1
    )


agentic_job_search_router = APIRouter()


class ResumeExtracted(BaseModel):
    candidate_name: str = Field(description="The full name of the candidate")
    skills: List[str] = Field(description="Top skills extracted from the resume")
    experience: List[str] = Field(description="Highlights of professional experience")
    education: List[str] = Field(description="Educational background")
    summary: str = Field(description="A brief professional summary of the candidate")


class ResumeMatchItem(BaseModel):
    label: str = Field(description="The requirement/keyword/skill being matched")
    matched: bool = Field(
        description="Whether the candidate possesses this requirement"
    )


class AnalysisResult(BaseModel):
    score: int = Field(description="Overall fit score from 0 to 100")
    recommendation: str = Field(description="One of: 'Hire', 'Consider', 'Reject'")
    job_role: str = Field(description="The target job role for the analysis")
    strengths: List[str] = Field(description="Top technical or professional strengths")
    weaknesses: List[str] = Field(description="Gaps or areas for improvement")
    suggestions: List[str] = Field(description="Actionable advice")
    reasoning: List[str] = Field(
        description="Bullet points explaining the score and recommendation"
    )
    extracted: ResumeExtracted = Field(description="Section-by-section extraction")
    match: List[ResumeMatchItem] = Field(
        description="Checklist of requirements vs candidate skills"
    )


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    resume_text: str
    analysis_result: Optional[AnalysisResult]


current_resume_context = {"text": ""}


def job_find_rag(docs):
    global current_resume_context
    full_text = "\n".join([doc.page_content for doc in docs])
    current_resume_context["text"] = full_text
    print(f"[INFO] Resume context updated. Character count: {len(full_text)}")
    return None


def run_analysis_with_fallback(state_messages: list):
    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            print(f"[AI] Attempting analysis with: {model_name}...")
            llm = get_llm(model_name)
            structured_llm = llm.with_structured_output(AnalysisResult)
            result = structured_llm.invoke(state_messages)
            print(f"[AI] Success with {model_name}!")
            return result
        except Exception as e:
            last_error = e
            error_msg = str(e).upper()
            if (
                "429" in error_msg
                or "QUOTA" in error_msg
                or "RESOURCE_EXHAUSTED" in error_msg
            ):
                print(f"[AI] Quota hit for {model_name}. Trying next...")
                continue
            elif "404" in error_msg or "NOT_FOUND" in error_msg:
                print(f"[AI] Model {model_name} not available (404). Trying next...")
                continue
            else:
                print(f"[AI] Unexpected error with {model_name}: {e}")
                continue

    if last_error:
        print(f"[AI] All models failed. Last error: {last_error}")
    raise last_error


def analyzer_node(state: MessagesState):
    resume_content = state.get("resume_text", current_resume_context["text"])

    print(
        f"[STEP 6.1] Preparing prompt with {len(resume_content)} chars of resume text."
    )

    prompt = f"""
    You are an expert HR and Technical Recruiter. You have been provided with the FULL text of a candidate's resume and a target job description.

    CANDIDATE RESUME:
    ---
    {resume_content}
    ---

    TASK:
    1. EXTRACT: Candidate Full Name, Target Job Role, Summary, Skills, Experience highlights, and Education details.
    2. MATCH: Identify 5-8 key job requirements and determine if the candidate matches them (label and matched: true/false).
    3. EVALUATE: 
       - Generate a score (0-100).
       - Give a recommendation: 'Hire' (80+), 'Consider' (60-79), 'Reject' (<60).
       - List key strengths and weaknesses.
       - Provide reasoning for your decision.
       - Provide actionable suggestions for the candidate.
    
    Be objective, thorough, and professional.
    """

    state_messages = [HumanMessage(content=prompt), *state["messages"]]

    try:
        result = run_analysis_with_fallback(state_messages)
        return {"analysis_result": result}
    except Exception as e:
        print(f"[CRITICAL] All fallback models failed: {e}")
        raise e


def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("analyze", analyzer_node)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)

    return builder.compile()


compiled_graph = build_graph()
resume_analysis_graph = compiled_graph
