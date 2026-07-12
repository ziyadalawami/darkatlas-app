# task number 4
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def generate_executive_report(asset_data: list) -> str:
    """
    Takes a list of asset dictionaries and generates a high-level markdown risk report.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b",
        temperature=0.1
    )

    system_message = SystemMessage(
        content=(
            "You are a Senior Security Architect. You will be provided with a raw list of technical assets. "
            "Write a concise, professional markdown report summarizing the external attack surface. "
            "Highlight the most critical assets, expose potential risks, and give a 2-3 sentence executive summary."
        )
    )

    human_template = "Raw Asset Data:\n{assets}"
    human_message = HumanMessagePromptTemplate.from_template(human_template)
    
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    chain = prompt | llm | StrOutputParser()
    
    try:
        return chain.invoke({"assets": str(asset_data)})
    except Exception as e:
        print(f"🚨 AI Report Generation Failed with error: {str(e)}")
        raise e
