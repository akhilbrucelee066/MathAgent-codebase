import os, json
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import re

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

with open('knowledge/maths_kb3.json', 'r') as f:
    MATH_KB = json.load(f)

with open(os.path.join(os.path.dirname(__file__), 'sys_prompt.txt'), 'r', encoding='utf-8') as f:
    system_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), 'math_words.csv'), 'r', encoding='utf-8') as f:
    math_keywords = set(line.strip().lower() for line in f if line.strip())

def is_math_question(text):
    if re.search(r'\d+\.?\d*', text):
        return True
    text_lower = text.lower()
    return any(word in text_lower for word in math_keywords)

# LLM
def is_basic_arithmetic_or_theory(query):
    arithmetic_pattern = r'^[\d\s\+\-\*/\(\)\.]+$'
    if re.match(arithmetic_pattern, query.strip()):
        return True
    theory_starts = [
        'what is', 'define', 'explain', 'who is', 'formula for', 'state', 'meaning of', 'describe', 'expand', 'find the value of'
    ]
    q_lower = query.strip().lower()
    return any(q_lower.startswith(start) for start in theory_starts)

# Web Search
def perform_web_search(query):
    if not SERPER_API_KEY:
        return "Web search is not available (API key missing)."
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = {"q": query, "gl": "in", "hl": "en"}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("organic", [])
        if not results:
            return "Sorry, I could not find a reliable answer online."
        snippet = results[0].get("snippet")
        link = results[0].get("link")
        return f"Web Search Result: {snippet}\n(Source: {link})"
    except Exception as e:
        return f"Web search error: {str(e)}"

# knowledge base
class rag:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.problems = [item['Problem'] for item in MATH_KB]
        if os.path.exists('knowledge/math_kb_embeddings.npy'):
            self.embeddings = np.load('knowledge/math_kb_embeddings.npy')
        else:
            self.embeddings = self.model.encode(self.problems)
            np.save('knowledge/math_kb_embeddings.npy', self.embeddings)

    def retrieve(self, query, threshold=0.76):
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        most_similar = np.argmax(similarities)
        if similarities[most_similar] > threshold:
            return MATH_KB[most_similar]
        return None

# maths professor
class math_agent:
    def __init__(self):
        self.history = [{"role": "system", "content": system_prompt}]
        self.rag = rag()

    def ask_agent(self, query):
        try:
            # query validating
            if not is_math_question(query):
                return "Sorry, I can only answer mathematics-related questions. Please ask a math question!! Articulate Query correctly!!"

            # answer directly with LLM
            if is_basic_arithmetic_or_theory(query):
                prompt = f"Student Question: {query}\nPlease answer this directly and simply as a math professor, without using any external knowledge base or web search."
                history = self.history + [{"role": "user", "content": prompt}]
                response = self.LLM(history)
                self.history.append({"role": "assistant", "content": response})
                return response + "\n\n Source: Direct LLM"

            # answer with RAG
            rag_response = self.rag.retrieve(query)
            if rag_response:
                verified_prompt = f"""Student Question: {query}\n\nI found a 'Similar Problem' in my Knowledge Base:\nProblem: {rag_response['Problem']}\nCategory: {rag_response.get('category', 'NO Category Provided')}\nAnnotated Formula: {rag_response.get('annotated_formula', 'No Formula Provided')}\nLinear Formula: {rag_response.get('linear_formula', 'No Formula Provided')}\nSolution Approach: {rag_response['Rationale']}\nJust apply the formula & approach the correct answer and present it to user in a specified Guiding way.\nUsing this reference, please provide a 'step-by-step' solution to the student's question in simple terms."""
                self.history.append({"role": "user", "content": verified_prompt})
                response = self.LLM(self.history)
                self.history.append({"role": "assistant", "content": response})
                return response + "\n\n Source: Knowledge Base"
            else:
                # human conformation for web_search
                return {"permission_required": True, "message": "I couldn't find this in my knowledge base. Would you like me to search the web for an answer?", "question": query}
        except Exception as e:
            return f"Error: {str(e)}"

    def LLM(self, history):
        try:
            response = client.chat.completions.create(
                messages=history,
                max_tokens=2025,
                model="llama-3.3-70b-versatile",
                temperature=0.3)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def present_web_answer(self, user_question, web_result):
        prompt = f"""Student Question: {user_question}\n\nHere is a web search result you can use as a reference:\n{web_result}\n\nCombine your own knowledge with the web result to answer the student's question in the most relevant and helpful way.\n- If the question is about problem-solving, approach, solution, derivation, or equation expansion, provide a step-by-step solution.\n- If the question is about theory, concept, definition, mathematicians, or general information, answer in clear points or paragraphs, focusing on clarity and relevance.\n- Do not repeat or rephrase the web result unnecessarily.\n- Use the web result only as a reference, not as the main answer.\n- Present the answer as if you are a knowledgeable math professor, using your own expertise and the web info as support."""
        history = self.history + [{"role": "user", "content": prompt}]
        response = self.LLM(history)
        self.history.append({"role": "assistant", "content": response})
        return response + "\n\n Source: Internet Source"
