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
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADbranch2\manager\datatesting.xlsx')

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
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADKbranch2\manager\datatesting.xlsx')

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
        
        df.to_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADKbranch2\manager\datatesting.xlsx', index=False)
        
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
    name="data_extractor",
    model=GEMINI_MODEL,
    description="An agent that extracts the relevant data that the user wants to update his dataset with from the conversation, summarizes the relevant data, and then formats it",
    instruction="""
    An agent that analyzes what new data the user wants to update his current dataset with and then formats it.

    This agent should determine how many updates the user wants to do, determine the Constituent ID (the row) that the user wants to update based
    on the output from the record locator, determine the correct column from the user's dataset that each update should update, and should extract the actual information that the user wants to update his dataset with for every single
    update that the user wants to upload. The user may just want to update one data from a record or multiple data from a record.

    This agent should determine which column the data for each update should update based on
    the possible column headers: Assigned To, Opportunity Name, Opportunity Purpose, Opportunity Status, Opportunity Assigned 
    To, Amount Asked, Date Asked, Amount Expected, Amount Funded, Date Funded, Last Action Category, Last Action Type, Last Action Date,
    Last Action Completed Date, Last Action Assigned To, Next Action Category, Next Action Type, Next Action Date, Next Action Assigned To.

    The agent should determine the relevant data that the user wants to update their
    dataset with for each update, and summarize this user data into wording that reflects wording found in
    standard opportunity files for donor data.

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
    description="An agent that locates the correct record to update",
    instruction="""
    An agent that determines which record the user wants to update.

    Use the information from the conversation to determine which constituent the user wants to make updates for, and ultimately
    determine the Consituent ID of the correct constituent.
    **************************************************************************
    The constituent name should be used to locate the correct record to update in the opportunity file by matching the constituent
    name to the constituent ID.

    The agent should use the locate_record_tool function to find the Constituent ID that is
    associated with the name provided.
    """,
    tools=[locate_opportunity_tool]
)

update_data_agent = SequentialAgent(
    name="update_data_agent",
    sub_agents=[record_locator,data_extractor, data_uploader],
    description="Updates the user's data by executing a sequence of extracting relevant data to be updated from the conversation, identifying the correct record(s) to update, and uploading the data into the user's dataset.",
)