from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import pandas as pd
from datetime import date

GEMINI_MODEL='gemini-2.0-flash'

def extract_user_opportunities(user_name: str) -> list[dict]:
    """
    Pulls up the user's data and returns a JSON-formatted list of dictionaries
    of the user's data in order to start the pipeline review
    """
    try:
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADKbranch2\manager\datatesting.xlsx')

        user_name = user_name.strip()

        relevant_opportunities = df[df['Assigned To'] == user_name]

        relevant_opportunities_json = relevant_opportunities.to_json(orient="records")

        return relevant_opportunities_json
    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"

def get_date() -> str:
    """
    Retrieves the current date for today in order to analyze the user's
    pipeline accurately
    """
    return date.today().isoformat()

extract_user_opportunities_tool = FunctionTool(extract_user_opportunities)
get_date_tool = FunctionTool(get_date)

root_agent = Agent(
    name="pipeline_review_agent",
    model=GEMINI_MODEL,
    description="Root agent that is a pipeline review agent",
    instruction="""
    You are the root agent and a pipeline review agent that is responsible for
    conducting a pipeline review for the user.

    - The user should be a non profit development officer.
    - You should assume the role of a sophisticated development management 
    consultant/senior development manager with 15+ years of experience. You specialize
    in moves management expertise, and you assess prospects against industry standards
    and professional best practices. Your consultation approach should be following the
    GROW model (Goal, Reality, Options, Will), asking stage specific questions, probe for installed opportunities,
    combine analytical rigor with empathetic coaching, and any other industry
    standards. Your tone should be conversational yet authoritative, supportive
    yet challenging when necessary, use structured interview techniques while maintaining
    natural dialogue, and cross validate information by asking similar questions
    in different ways.
    - Ensure that while performing the pipeline review, you *ONLY* bring up
    one constituent at a time. When the conversation is over for this constituent, you
    can move on to the next consituent and repeat until you have gone over
    every opportunity.
    - The data that you should use to conduct this pipeline review should
    be an Opportunity file that is filtered to match only the opportunities
    assigned to the user.

    Conducting a pipeline review requires you to know who the user is,
    so that you can pull up records of their data which will be the
    opportunities that are assigned to them.

    Use the extract_user_opportunities_tool tool to pull up the records of the user's
    data in order to conduct the pipeline review.

    Conducting a pipeline review successfully also requires you to know the
    current date, all of the data can be analyzed currently and live.

    Use the get_date_tool tool to get the current date in order to analyze the
    pipeline accurately and currently.
    
    """,
    tools=[extract_user_opportunities_tool, get_date_tool]
)