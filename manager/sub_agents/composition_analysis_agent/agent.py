from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import pandas as pd

GEMINI_MODEL='gemini-2.0-flash'

def analyze_opportunity_status() -> str:
    """
    Analyzes the distribution of the user's Opportunity Statuses for all of his constituents in his Opportunity
    file, and determines the composition of it.
    It counts the different statuses, calculates their percentage distribution,
    and returns a summary string. This function takes no arguments.
    """

    target_statuses = ['Cultivation', 'Solicitation', 'Stewardship', 'Qualification']
    
    try:
        df = pd.read_excel(r'C:\Users\justi\Desktop\School\Internship\internship\PipelineAI\agentfiles\googleADK\manager\data.xlsx')

        relevant_df = df[df['Opportunity Status'].isin(target_statuses)]

        total_relevant_count = len(relevant_df)
        
        status_counts = relevant_df['Opportunity Status'].value_counts()
        
        report_lines = [
            f"Here is the breakdown:"
        ]
        
        for status in target_statuses:
            count = status_counts.get(status, 0)
            percentage = (count / total_relevant_count) * 100
            
            report_lines.append(
                f"- {status}: {percentage:.1f}%"
            )
            
        # Join all lines into a single, multi-line string
        return "\n".join(report_lines)

    except Exception as e:
        return f"An unexpected error occurred while processing the file: {e}"


excel_analyzer_tool = FunctionTool(analyze_opportunity_status)


composition_analysis_agent = Agent(
    name="composition_analysis_agent",
    model=GEMINI_MODEL,
    description="An agent that can analyze the user's donor pipeline data and provide reports based on the data",
    instruction="""
    An agent that helps users analyze their CRM data and provides reports for them using the
    excel_analyzer_tool.
    This agent should assume the role of a sophisticated development management
    consultant/senior development manager with 15+ years of experience.
    The agent should also analyze the data and identify areas of improvement based on absolute
    expertise on this subject matter. To analyze this data, the agent will be an expert in moves
    management methodology and professional consultation frameworks
    """,
    tools=[excel_analyzer_tool]
)