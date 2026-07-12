# task number 3
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

class AssetClassification(BaseModel):
    environment: str = Field(description="Must be exactly one of: prod, staging, dev, or unknown")
    category: str = Field(description="The functional classification, e.g., web-server, api-endpoint, database, mail-server, dns-record")
    criticality: str = Field(description="Must be exactly one of: low, medium, high, or critical")
    suggested_tags: List[str] = Field(description="A list of 3-5 technical searchable labels based on the asset details")

def enrich_and_categorize_asset(asset_type: str, asset_value: str, metadata: dict) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b",  
        temperature=0.1
    )

    parser = JsonOutputParser(pydantic_object=AssetClassification)

    system_message = SystemMessage(
        content=(
            "You are an automated Attack Surface Management system. Your job is to classify "
            "incoming external technical assets precisely according to instructions. "
            "You must output raw JSON matching the requested schema exactly. Do not include markdown formatting or wrappers."
        )
    )

    human_template = """Analyze this asset and determine its environment, asset infrastructure category, criticality level, and logical tags.

Asset Type: {asset_type}
Asset Value: {asset_value}
Current Metadata: {metadata}

{format_instructions}"""
    
    human_message = HumanMessagePromptTemplate.from_template(human_template)
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    chain = prompt | llm | parser
    
    try:
        return chain.invoke({
            "asset_type": asset_type,
            "asset_value": asset_value,
            "metadata": str(metadata),
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        print(f"🚨 AI Categorization Failed with error: {str(e)}")
        raise e
