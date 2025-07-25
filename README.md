# Math Agent

### an Agentic mathematics  AI assistant powered by LLM, RAG & WEB

Math Agent is an agentic mathematics AI assistant designed to provide step-by-step solutions, explanations, and mathematical concepts. It combines large language models (LLMs), Retrieval-Augmented Generation (RAG), and web search to deliver accurate and context-aware answers to math queries.

## Overview

Math Agent leverages a hybrid approach:

- **LLM**: Uses Groq & models such as Gemini, GPT, or Llama-3 (configurable) for natural language understanding and reasoning.
- **RAG**: Integrates a knowledge base (MathQA dataset from Hugging Face) to retrieve relevant problems and solutions.
- **Web Search**: Utilizes the Serper API to fetch up-to-date information when the knowledge base is insufficient.
- **Feedback Loop**: Allows users to provide feedback to improve answer quality over time.

## Data & Frameworks

- **Data**: MathQA dataset (Hugging Face), custom knowledge base JSONs
- **Frameworks**: Python, FastAPI (backend), SentenceTransformers, Google Generative AI, requests, HTML/CSS/JS (frontend)

## Approach

1. User submits a math query via the web interface.
2. The agent first validates input as maths query or not. 
3. then, agent tries to attempt the answer using the LLM (LLM).
4. If not LLM then agent attempts to answer using the knowledge base (RAG).
5. If needed, it performs a web search for additional context (WEB).
6. The LLM orchestrates the final response, combining retrieved and generated information.
7. Users can provide feedback to help improve future responses.

## Usage

- pip install -r requirements.txt
- python app.py

For a detailed system design, diagrams, and documentation, see the landing page:

https://akhilbrucelee066.github.io/Math_Agent
