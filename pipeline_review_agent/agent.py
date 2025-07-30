from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import pandas as pd
from datetime import date
from .sub_agents.update_data_agent.agent import update_data_agent
import numpy as np

GEMINI_MODEL='gemini-2.0-flash'

def extract_user_opportunities(user_name: str) -> list[dict]:
    """
    Pulls up the user's data and returns a JSON-formatted list of dictionaries
    of the user's data in order to start the pipeline review
    """
    try:
        df = pd.read_excel('pipeline_review_agent/datatesting.xlsx')

        user_name = user_name.strip()

        relevant_opportunities = df[df['Assigned To'] == user_name].copy()

        for col in ["Constituent ID", "Amount Asked", "Amount Expected", "Amount Funded"]:
            if col in relevant_opportunities.columns:
                if relevant_opportunities[col].dtype in [np.float64, np.int64, float, int]:
                    if (relevant_opportunities[col].dropna() % 1 == 0).all():
                        relevant_opportunities.loc[:, col] = (
                            relevant_opportunities[col].fillna(0).astype(int)
                        )
        
        raw_dicts = relevant_opportunities.to_dict(orient="records")

        def sanitize_types(data):
            sanitized = []
            for row in data:
                clean_row = {}
                for key, value in row.items():
                    if pd.isna(value):
                        clean_row[key] = None  # Replace NaN with None (JSON null)
                    elif isinstance(value, (np.integer, np.int64, np.int32)):
                        clean_row[key] = int(value)
                    elif isinstance(value, (np.floating, np.float64, np.float32)):
                        clean_row[key] = int(value) if value.is_integer() else float(value)
                    elif isinstance(value, pd.Timestamp):
                        clean_row[key] = value.isoformat()  # Serialize datetime properly
                    else:
                        clean_row[key] = value
                sanitized.append(clean_row)
            return sanitized

        return sanitize_types(raw_dicts)
    
    except Exception as e:
        raise RuntimeError(f"Failed to extract opportunities: {e}")

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
    - You will update the user's database using the update_data_agent subagent whenever
    the user confirms changes they want to make to the data
    - The data that you should use to conduct this pipeline review should
    be an Opportunity file that is filtered to match only the opportunities
    assigned to the user.

    **MAKE SURE to ask the user about empty values for columns in each opportunity that you discuss. Try to get the user
    to provide information to fill into these empty values. Every opportunity that you talk about, the goal is also to
    not leave any value blank for the opportunity record.

    **DO NOT HALLUCINATE, and ESPECIALLY DO NOT HALLUCINATE DATES OR NUMBER VALUES**
    ONLY use the data from the opportunities file or the user when doing the pipeline review
    and analysis.

    **You MUST use the extract_user_opportunities_tool tool and the get_date_tool tool immediately after the user tells you
    their name, before you respond to them again.

    Conducting a pipeline review requires you to know who the user is,
    so that you can pull up records of their data which will be the
    opportunities that are assigned to them.

    Use the extract_user_opportunities_tool tool to pull up the records of the user's
    data in order to conduct the pipeline review.

    Conducting a pipeline review successfully also requires you to know the
    current date, all of the data can be analyzed currently and live.

    Use the get_date_tool tool to get the current date in order to analyze the
    pipeline accurately and currently.

    When the user suggests that he wants to update his data, collect all of the information necessary,
    confirm this with the user, and then use the update_data_agent subagent to complete this task.
    """,
    sub_agents=[update_data_agent],
    tools=[extract_user_opportunities_tool, get_date_tool]
)