from google.adk.agents import Agent, SequentialAgent, LlmAgent
from google.adk.tools import FunctionTool
import pandas as pd


GEMINI_MODEL='gemini-2.0-flash'

def locate_record(constituent_name: str) -> str:
    """
    Determines the correct record from the opportunity file that is associated with the constituent name that is passed
    into this function by finding the Constituent ID that is associated with that name.
    **THIS TOOL SHOULD ONLY BE RUN ONCE**
    """
    try:
        df = pd.read_excel('pipeline_review_agent/datatesting.xlsx')

        result = df.loc[df['Constituent Name'] == constituent_name, 'Constituent ID'].values

        if result.size > 0:
            return f"Record identified: Constituent ID = {result[0]}"
        else:
            return "Name not found"
        
    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"


def upload_data(relevant_data: list[dict]) -> str:
    """
    Updates the user's dataset by uploading the information that is passed into it into the user's dataset.
    This information may contain one specific value from a row to update, or multiple values for the same row.
    This tool should be passed a dictionary in JSON format.
    **THIS TOOL SHOULD ONLY BE RUN ONCE**
    """
    
    try:
        df = pd.read_excel('pipeline_review_agent/datatesting.xlsx')

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
        
        df.to_excel('pipeline_review_agent/datatesting.xlsx', index=False)
        
        return "Update successful. The data has been changed."

    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"

upload_data_tool = FunctionTool(upload_data)

locate_record_tool = FunctionTool(locate_record)


data_uploader = LlmAgent(
    name="data_uploader",
    model=GEMINI_MODEL,
    description="An agent that uploads the data that the user wants to update their dataset with using the JSON-formatted list of dictionaries that is output from the data_extractor agent",
    instruction="""
    An agent that takes the JSON-formatted list of dictionaries that is passed into it from the data_extractor agent and updates the user's dataset with this information.

    JSON-formatted list of dictionaries to update the dataset:
    {generated_data}

    This agent *MUST USE* the upload_data tool to complete the process of updating the user's dataset. Give the tool the JSON-formatted
    list of dictionaries that was created by the data_extractor. Only use the upload_data tool one time, do not run that tool more than once.

    After the tool has run, use the output from the tool as your response to the user.

    *ONLY RUN THE upload_data tool ONCE!!**
    """,
    tools=[upload_data_tool]
)

data_extractor = LlmAgent(
    name="data_extractor",
    model=GEMINI_MODEL,
    description="An agent that extracts the relevant data that the user wants to update his dataset with from the conversation and the locate_record_tool, summarizes the relevant data, and then formats it",
    instruction="""
    An agent that analyzes what new data the user wants to update his current dataset with and then formats it.

    You should assume the role of a sophisticated development management 
    consultant/senior development manager with 15+ years of experience. You specialize
    in moves management expertise, and you assess prospects against industry standards
    and professional best practices

    This agent should determine how many updates the user wants to do, determine the Constituent ID (the row) that the user wants to update based
    on the output from the locate_record_tool tool, determine the correct column from the user's dataset that each update should update, and should extract the actual information that the user wants to update his dataset with for every single
    update that the user wants to upload. The user may just want to update one data from a record or multiple data from a record.

    This agent should determine which column the data for each update should update based on
    the possible column headers: Assigned To, Opportunity Name, Opportunity Purpose, Opportunity Status, Opportunity Assigned 
    To, Amount Asked, Date Asked, Amount Expected, Amount Funded, Date Funded, Last Action Category, Last Action Type, Last Action Date,
    Last Action Completed Date, Last Action Assigned To, Next Action Category, Next Action Type, Next Action Date, Next Action Assigned To.

    The agent should determine the relevant data that the user wants to update their
    dataset with for each update, and summarize this user data into wording that reflects wording found in
    standard opportunity files for donor data.

    This may look like the user saying 'I want to plan my next action for John Smith to be a thank you phone call on August 10 2025', and then receiving
    output from the locate_record_tool function to identify the Constituent ID for John Smith as 10110. So, this agent should know that the user
    wants three updates to their data:
    Constituent ID: 10110, Column: Next Action Category, Value: Phone Call,
    Constituent ID: 10110, Column: Next Action Type, Value: Thank You, 
    Constituent ID: 10110, Column: Next Action Date, Value: 8/10/2025  12:00:00 AM

    The agent should reformat this collected and summarized data into a JSON array of dictionaries, containing
    each update and should be in this format:
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
    *ONLY output the JSON array of dictionaries

    Do not include any extra text or explanation, only the JSON array.

    Do not add any other text before or after the code block.
    """,
    output_key="generated_data"
)

record_locator = Agent(
    name="record_locator",
    model=GEMINI_MODEL,
    description="An agent that locates the correct record to update by finding the Constituent ID",
    instruction="""
    An agent that determines which record the user wants to update by finding the Constituent ID associated with the Constituent name.

    Use the information from the conversation to determine which constituent the user wants to make the updates for, and ultimately
    determine the Consituent ID of the correct constituent.

    Identify the name of the constituent that the user wants to update their data on and use that information to find the Constituent
    ID that matches the constituent name

    The constituent name should be used to locate the correct record to update in the opportunity file by matching the constituent
    name to the constituent ID.

    The agent should use the locate_record_tool tool to find correct record that the user wants to update by
    identifying the Constituent ID that is associated with the constituent name provided.
    **ONLY use the locate_record_tool tool once!! do not use it more than once.
    """,
    tools=[locate_record_tool]
)

update_data_agent = SequentialAgent(
    name="update_data_agent",
    sub_agents=[record_locator,data_extractor, data_uploader],
    description="Updates the user's data by executing a sequence of extracting relevant data to be updated from the conversation, identifying the correct record(s) to update, and uploading the data into the user's dataset.",
)