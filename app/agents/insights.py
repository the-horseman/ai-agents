from ..tools.insights import insight_tools
from ..llm.bedrock import llm
from .agents import create_tool_agent

lethalityPrompt = """Determinism and Lethality of Indicators of Compromise (IOC):
Determinism:
This score reflects how unique an IOC is to a specific campaign or threat group. It indicates how likely an IOC found in an environment belongs to a particular campaign.
Possible Values:
99 (Very unique): The IOC is highly specific and strongly associated with the campaign.
70 (Unique): The IOC is used in multiple campaigns but remains unique to this specific threat group.
50 (Partly unique): IOC may have unique segments but is not entirely specific to the campaign.
30 (Commodity): The IOC is widely used across campaigns and threat groups, with minimal uniqueness.
20 (Non-deterministic): The IOC is commonly used but not malicious.
10 (Unknown): There is insufficient data to classify the IOC's uniqueness.
Lethality:
This score evaluates the destructive potential of an IOC, indicating how dangerous it is.
Possible Values:
99 (Destructive): The IOC is confirmed to be highly malicious and destructive.
70 (Malicious): The IOC is definitely malicious but less destructive.
50 (Malicious enabler): Malicious tools leave behind artifacts but may not be destructive themselves.
30 (Probable malicious): Analysis suggests it is likely malicious, but no direct sample is available.
20 (Dual use): A legitimate tool used for malicious purposes.
10 (Unconfirmed): Lack of data or samples to confirm the IOC's lethality.
"""

insight_reporting_agent = create_tool_agent(
    llm=llm, tools=insight_tools,
    system_message="""
    Find me the all the related information to events. You must analyze all the IOCs that are given to you.
    You have no prior knowldge about any of the above mentioned details and should always use the tools given to you.
    Once you find the above details about all the IOCs and the files, write a detailed report in markdown format for a SOC analyst.
    IMPORTANT: ALL the indicators of compromise you can find from <events>. 
    Types of Supported IOCs are - MD5, SHA256, SHA512, URL, IP, Domain, Hostname.
    Use below information and generate Determinism and Lethality scores.\n {lethalityPrompt}\n.
    Write a report in markdown format that has the answer to the folowing questions based upon the events. 
    Are the Events actually a threat or suspicious? 
    If YES 
        Which Host was this Detected First? 
        Call out the Problem Process and any other suspicious processes if any. Eg. The cmd.exe(pid:1011) is the problem process. 
        Where should the Investigation start? 
        How To Investigate? 
    Else 
        Why Not?
    What are the Suspicious process names?
    Remember to include Pid or Process Id. 
    What are the Relations among the Events? 
    What Suspicious and Misinterpreted benign actions do the Events imply?
    Mention the summary of the tools responses under 'Insights' heading.
    NOTE: Do NOT write any questions as you do not have access to the tools required to do so.
    The report should ONLY contain the following Sections: 
    1. Complete Flow of Events
    2. The problem process and Why? 
    3. Suspicious Processes 
    4. Key Points
    5. Insights
    6. Device Details.
    While Creating the report keep in mind to have as many citations as possible for any claim that you make. 
    For example process names, command lines, process ids, usernames, api calls, regsitery names, IP addresses etc."""
)
