import os
from langchain_core.messages import HumanMessage
from agents.resume_analysis_agent import run_analysis_with_fallback, AnalysisResult
from dotenv import load_dotenv

load_dotenv()


def test_fallback():
    print("--- Testing Agent Fallback Logic ---")
    test_message = [
        HumanMessage(
            content="Hello, give me a dummy resume analysis for 'Software Engineer'."
        )
    ]
    try:
        result = run_analysis_with_fallback(test_message)
        print(f"✅ Success! Result type: {type(result)}")
        if isinstance(result, AnalysisResult):
            print(f"Score: {result.score}")
            print(f"Recommendation: {result.recommendation}")
    except Exception as e:
        print(f"❌ All models failed during test: {e}")


if __name__ == "__main__":
    test_fallback()
