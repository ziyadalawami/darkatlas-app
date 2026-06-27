import os
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

# ==========================================
# 1. DEFINE THE TOOLS
# ==========================================
@tool
def query_internal_database(search_request: str) -> str:
    """
    Use this tool to search the internal Attack Surface Management (ASM) database.
    Pass a natural language string describing what you are looking for 
    (e.g., 'Find all critical domains', 'Show me active staging assets').
    """
    try:
        # The agent literally calls your Task 1 API endpoint!
        response = requests.post(
            "http://127.0.0.1:8000/api/v1/assets/query",
            json={"query": search_request},
            timeout=10
        )
        if response.status_code == 200:
            return str(response.json().get("assets", "No assets found."))
        return f"Database query failed with status {response.status_code}"
    except Exception as e:
        return f"Tool execution error: {str(e)}"

# ==========================================
# 2. BUILD THE AGENT
# ==========================================
def run_autonomous_security_agent(user_prompt: str) -> str:
    """
    Takes a user question, decides if it needs to query the database,
    fetches the data, and returns a final analysis.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # We use a tool-compatible model configuration
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b", 
        temperature=0.1
    )

    tools = [query_internal_database]

    # The prompt instructs the agent on HOW to behave
    prompt = ChatPromptTemplate.from_messages([
        (
            "system", 
            "You are an autonomous Senior Security Architect. You have access to a tool "
            "that queries an internal asset database. If the user asks about our assets, "
            "you MUST use your tool to look them up before answering. Base your final "
            "security assessment strictly on the data returned by the tool."
        ),
        ("human", "{input}"),
        # This scratchpad is where the LLM does its "thinking" and stores tool outputs
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Bind everything together
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # The executor runs the loop: Think -> Use Tool -> Observe Result -> Final Answer
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    try:
        result = agent_executor.invoke({"input": user_prompt})
        return result["output"]
    except Exception as e:
        print(f"🚨 Agent Execution Failed: {str(e)}")
        raise e
