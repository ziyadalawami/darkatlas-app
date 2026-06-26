# task number 1
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

# The safe, structured filter format the AI will return
class AssetQueryFilter(BaseModel):
    asset_type: Optional[str] = Field(None, description="The type of asset, e.g., subdomain, ip, domain")
    environment: Optional[str] = Field(None, description="e.g., prod, staging, dev")
    criticality: Optional[str] = Field(None, description="e.g., critical, high, medium, low")
    tags: Optional[List[str]] = Field(None, description="Specific keywords like 'expired-certificate', 'nginx'")

def translate_nl_query(user_query: str) -> dict:
    """
    Translates a plain-English search query into a structured JSON filter dictionary.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b",
        temperature=0.0 # Zero creativity, strictly extract facts
    )

    parser = JsonOutputParser(pydantic_object=AssetQueryFilter)

    system_message = SystemMessage(
        content="You are a query translator for a cybersecurity database. Translate the user's natural language request into the exact JSON schema provided. If a field is not mentioned, leave it null."
    )

    human_template = """User Query: "{user_query}"\n\n{format_instructions}"""
    human_message = HumanMessagePromptTemplate.from_template(human_template)
    
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    chain = prompt | llm | parser
    
    try:
        return chain.invoke({
            "user_query": user_query,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        print(f"🚨 AI Query Failed with error: {str(e)}")
        raise e
