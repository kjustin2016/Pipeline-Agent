from google.adk.agents import Agent, SequentialAgent, LlmAgent
from google.adk.tools import FunctionTool
import pandas as pd


GEMINI_MODEL='gemini-2.0-flash'

def locate_opportunity(constituent_name: str) -> str:
    """
    Determines the opportunity from the opportunity file that is associated with the name that is passed
    into this function by finding the Constituent ID that is associated with that name.
    """
    try:
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADK\manager\datatesting.xlsx')

        result = df.loc[df['Constituent Name'] == constituent_name, 'Constituent ID'].values

        if result.size > 0:
            return f"Opportunity identified: Constituent ID = {result[0]}"
        else:
            return "Name not found"
        
    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"


def upload_data(relevant_data: list[dict]) -> str:
    """
    Updates the user's dataset by uploading the information that is passed into it into the user's dataset.
    This information may contain one specific value from a row to update, or multiple values for the same row.
    This tool should be passed a dictionary in JSON format.
    """
    
    try:
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADK\manager\datatesting.xlsx')

        df['Constituent ID'] = df['Constituent ID'].astype(int)

        for item in relevant_data:
            constituent_id = int(item["Constituent ID"])
            column = item["Column"]
            value = item["Value"]

            if column in ["Amount Asked", "Amount Expected", "Amount Funded"]:
                value = float(value)
            elif column == "Constituent ID":
                value = int(value)
            elif column in [
                "Date Asked", "Date Funded", "Last Action Date",
                "Last Action Completed Date", "Next Action Date"
            ]:
                try:
                    if isinstance(value, (int, float)) and len(str(int(value))) >= 13:
                        value = pd.to_datetime(value, unit='ms')
                    else:
                        value = pd.to_datetime(value, errors='coerce')
                except Exception:
                    value = pd.NaT
            
            df.loc[df["Constituent ID"] == constituent_id, column] = value
        
        df.to_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADK\manager\datatesting.xlsx', index=False)
        
        return "Update successful. The data has been changed."

    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"

upload_data_tool = FunctionTool(upload_data)

locate_opportunity_tool = FunctionTool(locate_opportunity)


data_uploader = LlmAgent(
    name="data_uploader",
    model=GEMINI_MODEL,
    description="An agent that uploads the JSON-formatted list of dictionaries that is passed into it into the user's dataset",
    instruction="""
    An agent that takes the JSON-formatted list of dictionaries that is passed into it and updates the user's dataset with this information.

    JSON-formatted list of dictionaries to update the dataset:
    {generated_data}

    This agent *MUST USE* the upload_data tool to complete the process of updating the user's dataset.

    After the tool has run, output the result from the tool as your final answer.
    """,
    tools=[upload_data_tool]
)

data_extractor = LlmAgent(
    name="data_extractor_agent",
    model=GEMINI_MODEL,
    description="An agent that takes the user's response and extracts and summarizes the relevant data, and formats it",
    instruction="""
    An agent that analyzes and formats the new data that the user wants to update their dataset with.

    This agent should determine the Constituent ID, the correct column from the user's dataset that this new data
    belongs in, and extract the actual information that the user wants to put in
    their dataset, and then format this data.

    This agent should determine which column the data should be updating based on
    the possible column headers: Assigned To, Opportunity Name, Opportunity Purpose, Opportunity Status, Opportunity Assigned 
    To, Amount Asked, Date Asked, Amount Expected, Amount Funded, Date Funded, Last Action Category, Last Action Type, Last Action Date,
    Last Action Completed Date, Last Action Assigned To, Next Action Category, Next Action Type, Next Action Date, Next Action Assigned To.

    The agent should determine the relevant data that the user wants to update their
    dataset with, and summarize this user data into wording that reflects wording found in
    standard opportunity files for donor data.

    The agent should reformat this collected and summarized data into a JSON format.

    After reformatting, Output *only* the data as a JSON array of dictionaries in this format:

[
  {
    "Constituent ID": 412161,
    "Column": "Next Action Date",
    "Value": "2025-09-30"
  },
  {
    "Constituent ID": 412161,
    "Column": "Next Action Type",
    "Value": "Phone Call"
  }
]

    Do not include any extra text or explanation, only the JSON array.

    Do not add any other text before or after the code block.
    """,
    output_key="generated_data"
)

data_upload_pipeline_agent = SequentialAgent(
    name="data_upload_pipeline_agent",
    sub_agents=[data_extractor, data_uploader],
    description="Executes a sequence of extracting relevant data and uploading it into the user's dataset.",
)

opportunity_identifier = Agent(
    name="opportunity_identifier",
    model=GEMINI_MODEL,
    description="An agent that identifies which opportunity the user wants to update",
    instruction="""
    An agent that determines which opportunity the user wants to update.

    The name of the constituent that the opportunity is correlated with should be provided,
    and that name should be used to locate the opportunity in the opportunity file. The agent should
    find the Constituent ID to identify the opportunity.

    The agent should use the locate_opportunity function to find the Constituent ID that is
    associated with the name provided.
    """,
    tools=[locate_opportunity_tool]
)

data_update_manager_agent = Agent(
    name='data_update_manager_agent',
    model=GEMINI_MODEL,
    description="Data update manager agent",
    instruction="""
    You are the manager agent that is responsible for facilitating the updating of the user's dataset and for
    identifying which opportunity the user would like to update.

    This agent should assume the role of a sophisticated development management
    consultant/senior development manager with 15+ years of experience.

    The agent should first discover the opportunity associated with the constituent name, and then
    should update the user's dataset for his opportunities.

    Interact with the user and determine if you should transfer to other agents. Use your best judgement
    to determine which agent to delegate to.

    Send the user to the data_upload_pipeline_agent when they are ready to
    update their data and have confirmed the values they want to update.

    You are responsible for delegating tasks to the following agent:
    - data_upload_pipeline_agent
    - opportunity_identifier
    """,
    sub_agents=[data_upload_pipeline_agent, opportunity_identifier]
)
