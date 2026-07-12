# task number 2
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def analyze_asset_vulnerability(asset_type: str, asset_value: str, metadata: dict) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b", 
        temperature=0.1
    )

    system_message = SystemMessage(
        content=(
            "You are an expert Attack Surface Management (ASM) and threat intelligence analyst. "
            "Your goal is to provide concise, high-impact security assessments focusing on attack vectors, "
            "next steps for an attacker, and actionable mitigations. Keep it highly technical."
        )
    )

    human_template = """Analyze the following external asset for potential security risks, entry points, and misconfigurations:
    
Asset Type: {asset_type}
Asset Value: {asset_value}
Contextual Metadata: {metadata}"""
    
    human_message = HumanMessagePromptTemplate.from_template(human_template)
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    chain = prompt | llm | StrOutputParser()
    
    try:
        return chain.invoke({
            "asset_type": asset_type,
            "asset_value": asset_value,
            "metadata": str(metadata)
        })
    except Exception as e:
        print(f"🚨 AI Analysis Failed with error: {str(e)}")
        raise e
