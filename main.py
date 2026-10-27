
import os
import json
from typing import TypedDict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

load_dotenv()


# 1. Shared state passed between all four nodes
class JobState(TypedDict, total=False):
    job_description: str
    extracted_info: dict[str, Any]
    classification: dict[str, Any]
    skill_analysis: dict[str, Any]
    hiring_report: dict[str, Any]
    error: str


# Groq model

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )



# Convert model response into a Python dictionary
def ask_for_json(prompt: str) -> dict:
    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )

    content = str(content).strip()
    content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("AI did not return valid JSON.")

    result = json.loads(content[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError("AI response must be a JSON object.")

    return result


# Node 1: Information Extraction
def extract_information(state: JobState) -> dict:
    prompt = f"""
Analyze this job description and extract the requested information.

Return ONLY a valid JSON object with these keys:
job_title, company_name, required_experience, required_skills.

Use "Not specified" when information is missing.
required_skills must be a list of strings.

Job description:
{state["job_description"]}
"""
    result = ask_for_json(prompt)
    return {"extracted_info": result}


# Node 2: Job Classification
def classify_job(state: JobState) -> dict:
    prompt = f"""
Classify the following job using the extracted information.

Return ONLY a valid JSON object with these keys:
job_category, employment_type, work_mode.

job_category examples: Artificial Intelligence, Web Development,
Data Science, Mobile Development, Cybersecurity, Other.
employment_type: Full-time, Part-time, Internship, Contract,
or Not specified.
work_mode: Remote, Hybrid, On-site, or Not specified.

Job information:
{json.dumps(state.get("extracted_info", {}))}
Original description:
{state["job_description"]}
"""
    return {"classification": ask_for_json(prompt)}


# Node 3: Skill Analysis
def analyze_skills(state: JobState) -> dict:
    prompt = f"""
Analyze the skills required for this job.

Return ONLY a valid JSON object with:
technical_skills: list of strings,
soft_skills: list of strings,
top_3_skills: list of exactly 3 strings when possible.

Use the job description and extracted information.
Do not invent skills that are unrelated to the role.

Extracted information:
{json.dumps(state.get("extracted_info", {}))}

Job description:
{state["job_description"]}
"""
    result = ask_for_json(prompt)

    for key in ("technical_skills", "soft_skills", "top_3_skills"):
        if not isinstance(result.get(key), list):
            result[key] = []

    return {"skill_analysis": result}


# Node 4: Generate structured hiring report
def generate_hiring_report(state: JobState) -> dict:
    return {
        "hiring_report": {
            "job_title": state.get("extracted_info", {}).get(
                "job_title", "Not specified"
            ),
            "company_name": state.get("extracted_info", {}).get(
                "company_name", "Not specified"
            ),
            "required_experience": state.get(
                "extracted_info", {}
            ).get("required_experience", "Not specified"),
            "required_skills": state.get(
                "extracted_info", {}
            ).get("required_skills", []),
            "job_category": state.get("classification", {}).get(
                "job_category", "Not specified"
            ),
            "employment_type": state.get("classification", {}).get(
                "employment_type", "Not specified"
            ),
            "work_mode": state.get("classification", {}).get(
                "work_mode", "Not specified"
            ),
            "technical_skills": state.get(
                "skill_analysis", {}
            ).get("technical_skills", []),
            "soft_skills": state.get(
                "skill_analysis", {}
            ).get("soft_skills", []),
            "top_3_skills": state.get(
                "skill_analysis", {}
            ).get("top_3_skills", []),
        }
    }


# Build the LangGraph workflow
builder = StateGraph(JobState)

builder.add_node("information_extraction", extract_information)
builder.add_node("job_classification", classify_job)
builder.add_node("skill_analysis", analyze_skills)
builder.add_node("hiring_report", generate_hiring_report)

builder.add_edge(START, "information_extraction")
builder.add_edge("information_extraction", "job_classification")
builder.add_edge("job_classification", "skill_analysis")
builder.add_edge("skill_analysis", "hiring_report")
builder.add_edge("hiring_report", END)

job_graph = builder.compile()


# Function called by the Streamlit UI
def analyze_job(description: str) -> dict:
    if not description or not description.strip():
        raise ValueError("Please enter a job description.")

    if len(description.strip()) < 30:
        raise ValueError(
            "Please enter a more detailed job description (at least 30 characters)."
        )

    initial_state: JobState = {
        "job_description": description.strip()
    }

    result = job_graph.invoke(initial_state)
    return result["hiring_report"]
