from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient


import streamlit as st

import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search(query: str, num_results: int = 2, max_chars: int = 500) -> list:  # type: ignore[type-arg]
    if not api_key or not search_engine_id:
        raise ValueError("API key or Search Engine ID not found in environment variables")

    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {"key": str(api_key), "cx": str(search_engine_id), "q": str(query), "num": str(num_results)}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(response.json())
        raise Exception(f"Error in API request: {response.status_code}")

    results = response.json().get("items", [])

    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return ""

    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {"title": item["title"], "link": item["link"], "snippet": item["snippet"], "body": body}
        )
        time.sleep(1)  # Be respectful to the servers

    return enriched_results

def analyze_jd_cv() -> dict:
    enriched_results = []
    enriched_results.append({"Job Description": text1})
    enriched_results.append({"CV": text2})
    print(enriched_results)
        
    return enriched_results

# Title for the app
st.title("AI Agent Interview")

# First big text box
text1 = st.text_area("Enter Job Description", height=200, placeholder="Type or paste your text here...")

# Second big text box
text2 = st.text_area("Enter Resume", height=200, placeholder="Type or paste your text here...")

# Combine button
if st.button("Combine Texts"):
    # Combine the two texts
    # combined_text = text1 + "\n\n" + text2

    # Display the combined text
    st.subheader("Combined Text")
    

    google_search_tool = FunctionTool(
    google_search, description="Search Google for information, returns results with a snippet and body content")

    jd_analysis_tool = FunctionTool(analyze_jd_cv, description="Combine the job description, and cv.")

    search_agent = AssistantAgent(
    name="Google_Search_Agent",
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    tools=[google_search_tool],
    description="Search Google for information, returns top 5 results with a snippet and body content",
    system_message="You are a helpful AI assistant. Solve tasks using your tools.",)

    stock_analysis_agent = AssistantAgent(
        name="Job_Description_Analysis_Agent",
        model_client=OpenAIChatCompletionClient(model="gpt-4o"),
        tools=[jd_analysis_tool],
        description="Analyze job description, CV, and list of questions, and provide me list of 5 most appropriate questions",
        system_message="You are a helpful assistant which takes list of questions, CV, and job description, then maps most relevant 5 questions to job description.",
    )


    # report_agent = AssistantAgent(
    #     name="Report_Agent",
    #     model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    #     description="Take a role given, and generate a list of questions for the same",
    #     system_message="You are a helpful assistant that take questions from the list, and select top 2 questions mapped to job description and resume. When you done with generating the report, reply with TERMINATE.",
    # )

    team = RoundRobinGroupChat([search_agent,stock_analysis_agent], max_turns=2)

    stream = team.run_stream(task="Give the list of questions for Senior Data Scientist")

    async def main1(stream) -> None:
        async for message in stream:
            st.write(message)
    import asyncio
    asyncio.run(main1(stream))