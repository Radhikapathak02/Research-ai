# Research AI

A multi-agent AI research system that automates web research using specialized agents for search, source analysis, report generation, and critical review.

## Tech Stack

- Python
- LangChain
- OpenAI
- Tavily
- BeautifulSoup
- Streamlit

## Features

- Web search using Tavily
- Source scraping and analysis
- AI-generated research reports
- Automated report critique
- Streamlit-based user interface

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/research-ai.git
cd research-ai
pip install -r requirements.txt

Create a .env file and add your API keys:

OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
Run
python -m streamlit run app.py