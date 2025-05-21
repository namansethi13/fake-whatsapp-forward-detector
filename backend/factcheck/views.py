from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from pydantic import BaseModel, Field
from langchain_community.tools import TavilySearchResults
import pytz
from datetime import datetime
from langchain.tools import tool
from langchain.agents import initialize_agent
from langchain.output_parsers import PydanticOutputParser

@tool
def get_today_date(format : str = "%Y-%m-%d"):
    """
    Outputs todays date 
    """
    return datetime.now().strftime(format)




def remove_decorations(text):
    lower = text.strip().lower()
    res = ""
    for c in lower:
        if c in "_*~'''->`":
            continue
        if c == "\n":
            res += " "
        else:
            res += c
    return res


class Claim(BaseModel):
    isClaim: bool = Field(
        description="Whether the text contains a claim or not.",
        example=True,
    )
    claim: str = Field(
        description="The claim to be fact-checked. The claim should be a single sentence.",
        example="The sky is blue.",
    )

class ScoreAndComments(BaseModel):
    score: int = Field(
        description="Given a claim how and you confident you are that is is true, 0 means completely false and 10 means completely true", 
        example="3",
        ge=0,
        le=10
    )
    comments: str = Field(
        description="Comments the LLM has about the claim",
        example="This information is a known fact and completely true"
    )

def extract_claim(text):
    ClaimLLM = ChatGoogleGenerativeAI(temperature=0.7, model="gemini-2.0-flash")
    StructuredClaimLLM = ClaimLLM.with_structured_output(Claim)
    fact_system_prompt = SystemMessage(
        content="You are a part of the fact-checking assistant. You will be given a text and you need to check if it contains any claims. If it does, return the claim. If it doesn't, return 'No claims found'."
    )
    fact_human_prompt = HumanMessagePromptTemplate.from_template(
        "Check the following text for claims and list them out as a text can have multiple claims: {text}",
        input_variables=["text"]
    )
    fact_check_prompt = ChatPromptTemplate.from_messages(
        [
            fact_system_prompt,
            fact_human_prompt,
        ]
    )
    fact_chain = (
        fact_check_prompt | 
        StructuredClaimLLM |
        {
            "isClaim": lambda x: x.isClaim,
            "claim": lambda x: x.claim,
        }
    )

    claim = fact_chain.invoke({"text": text})
    return claim  


def fact_check(claim_obj : dict) -> dict:
    LLM = ChatGoogleGenerativeAI(temperature=0.8, model="gemini-2.0-flash")
    ToolLLM = ChatGoogleGenerativeAI(temperature=0.3, model="gemini-2.0-flash")
    StructuredClaimLLM = LLM.with_structured_output(ScoreAndComments)
    fact_system_prompt = SystemMessage(
        content="You are a part of the fact-checking assistant. Given a claim you need to fact check it by searching the internet a tool is provided to you for that, you have to make sure you check it with the current date if it is a fact that can change overtime, provide a score between 0-10 based on how true is it and a sentence related to what you think, your comments can include telling a short description, followed by what you think about it, answer rationally and be factual"
        
    )
    fact_human_prompt = HumanMessagePromptTemplate.from_template(
        "{claim}",
        input_variables=["claim"]
    )
    prompt = ChatPromptTemplate.from_messages([
        fact_system_prompt,
        fact_human_prompt
    ]
    )
    search_tool = TavilySearchResults()
    tools= [search_tool, get_today_date]
    agent = initialize_agent(tools=tools , llm=ToolLLM , agent_type="zero-shot-react-description", verbose=True)

    chain =(
        prompt
        |
        agent
        
    )   

    res = chain.invoke(claim_obj)
    output = StructuredClaimLLM.invoke(res["output"])


    return output



@api_view(['POST', 'GET'])
def factCheck(request):
    if request.method == 'POST':
        if 'text' not in request.data:
            return Response({"error": "text parameter is required"}, status=400)
        clean_text = request.data.get('text')
        claim = extract_claim(clean_text)
        if claim['isClaim'] == False or claim['claim'] == "No claims found":
            return Response({"message": "No claims found"}, status=404)

        res = fact_check(claim)
        print(res)
        return Response({"res": res})

    if request.method == 'GET':
        return Response({"message": "Please use POST method to send the text for fact-checking."})

   
