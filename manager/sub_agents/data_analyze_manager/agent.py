from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from datetime import date
import pandas as pd

GEMINI_MODEL='gemini-2.0-flash'

def get_date() -> str:
    """
    Determine's today's current date.
    """
    try:
        today = date.today()
        return today.isoformat()
    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"
    
def find_relevant_opportunities(user_name: str) -> list[dict]:
    """
    Use the user's name to identify which opportunities are associated with them. Finds opportunities in which the user's name
    matches the 'Assigned To' name.
    """
    try:
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADKbranch2\manager\datatesting.xlsx')

        user_name = user_name.strip()

        relevant_opportunities = df[df['Assigned To'] == user_name]

        relevant_opportunities_json = relevant_opportunities.to_json(orient="records")

        return relevant_opportunities_json
    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"


get_date_tool = FunctionTool(get_date)

find_relevant_opportunities_tool = FunctionTool(find_relevant_opportunities)

relevant_opportunity_identifier = Agent(
    name='relevant_opportunity_identifier',
    model=GEMINI_MODEL,
    description='An agent that identifies relevant opportunities based on the users name and also determines the priority of the opportunities',
    instruction="""
    You are an agent that identifies the relevant opportunities from the opportunity file that are associated with the user's name and then
    determines the priority of all of these opportunities.

    You are a sophisticated Development Management Consultant with 15+ years of experience in moves management methodology and 
    professional consultation frameworks. You specialize in:

    MOVES MANAGEMENT EXPERTISE:
    - Five distinct stages: identification, qualification, cultivation, solicitation, and stewardship
    - Each stage has specific entry criteria, typical activities, and advancement triggers
    - Assess prospects against industry standards and professional best practices

    You will be passed the user's name and the current date, and will use this information to identify opportunties and determine priority.

    The agent should use the find_relevant_opportunities_tool to identify the relevant opportunities using the name of the user.

    The output of the find_relevant_opportunities_tool will be a JSON-formatted list of dictionaries of the relevant opportunities. Use
    this JSON-formatted list of dictionaries to determine the priority of these relevant opportunities.

    The agent should then determine the priority of these relevant opportunities. The agent should use its absolute expertise on the topic
    and use industry standards and best practices to determine which opportunities should have top priority, as well as retaining knowledge of the
    current date to help determine the priority of these opportunities. Make sure to reorder the opportunties and keep them formatted as a
    JSON-formatted list of dictionaries as the output.

    **ONLY output the JSON-formatted list of dictionaries for the relevant opportunties that have been reordered by priority after all previous
    instructions are finished. Do not include any text before or after the JSON-formatted list of dictionaries, **ONLY output the JSON-formatted list of dictionaries.
    
    Return back to the data_analyze_manager agent when everything is finished and after you get your output.
    """,
    tools=[find_relevant_opportunities_tool]
)

data_analyze_manager = Agent(
    name='data_analyze_manager',
    model=GEMINI_MODEL,
    description="Data analyze manager agent",
    instruction="""
    You are the manager agent that is responsible for facilitating the identification of opportunities that are associated with the user's name, the
    reformatting of the relevant opportunity data into a JSON-formatted list of dictionaries, and the determination of the priority of these opportunities.

    You are also responsible for finding today's date.

    The agent should first determine the current date for today, and then it should identify the relevant opportunities related to the user's
    name, reformat this relevant opportunity data into a JSON-formatted list of dictionaries, find the priority of these relevant opportunities,
    and then reorder the opportunities based on priority.

    In order to determine the current date for today, the agent shall use the get_date function to find this.

    The agent shall then delegate the task to the relevant_opportunity_identifier to identify the user's relevant opportunities, reformat this relevant
    opportunity data into a JSON-formatted list of dictionaries, find the priority of these opportunities, and reorder the opportunities based on priority.

    This agent should pass the result of the get_date function and should pass the user's name into the relevant_opportunity_identifier, so
    that the relevant_opportunity_identifier can use that information to find the relevant opportunities and determine the priority of the opportunities.

    This agent should *ONLY* return the JSON formatted and reordered relevant opportunities after
    the relevant opportunities are found and the opportunities are reordered based on priority.

    This agent should *ONLY* output the JSON-formatted list of dictionaries for relevant opportunities after the previous instructions are finished.

    You are responsible for delegating tasks to the following agent:
    - opportunity_identifier

    After everything is done, return to the root agent.
    """,
    tools=[get_date_tool],
    sub_agents=[relevant_opportunity_identifier]
)
