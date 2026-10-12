import os
import re
from typing import List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Service for interacting with Groq LLM API."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")
        self._context: Dict[str, List[Dict]] = {}  # session_id -> messages

    def _need_key(self):
        return {"response": "GROQ_API_KEY is not configured. Set it in env to enable AI features.", "session_id": "default", "error": True}

    def chat(self, message: str, session_id: str = "default",
             context_docs: Optional[List[Dict]] = None) -> Dict:
        """Send a chat message and get a response."""
        if self.client is None:
            return {"response": "GROQ_API_KEY is not configured. Set it in env to enable AI features.", "session_id": session_id, "error": True}
        if session_id not in self._context:
            self._context[session_id] = []

        user_msg = {"role": "user", "content": message}

        messages = list(self._context[session_id])

        if context_docs:
            doc_context = "\n\n".join([
                f"[Document: {d.get('source', 'unknown')}]\n{d.get('text', '')}"
                for d in context_docs[:3]
            ])
            system_prompt = (
                "You are a helpful AI study assistant. Use the following document "
                "context to answer the student's question. If the answer is not in the "
                "documents, say so honestly and provide a general answer if you can. "
                "Provide clear, structured explanations with examples when helpful.\n\n"
                f"Document Context:\n{doc_context}"
            )
            messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            system_prompt = (
                "You are a helpful AI study assistant and tutor. Answer questions clearly "
                "and accurately based on your general knowledge. For study-related questions, "
                "provide structured explanations with examples. If you're unsure about something, "
                "say so honestly."
            )
            messages = [{"role": "system", "content": system_prompt}] + messages

        messages.append(user_msg)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9,
            )
            assistant_msg = response.choices[0].message.content

            self._context[session_id].append(user_msg)
            self._context[session_id].append({
                "role": "assistant",
                "content": assistant_msg
            })

            if len(self._context[session_id]) > 20:
                self._context[session_id] = self._context[session_id][-20:]

            return {
                "response": assistant_msg,
                "session_id": session_id,
                "model": self.model
            }

        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}. "
                            "Please check your API key and try again.",
                "session_id": session_id,
                "error": True
            }

    def clear_context(self, session_id: str):
        """Clear conversation context for a session."""
        if session_id in self._context:
            del self._context[session_id]

    def generate_quiz_questions(self, context: str, num_questions: int = 5,
                                topic: str = "") -> List[Dict]:
        """Generate multiple-choice quiz questions from context."""
        prompt = (
            f"Generate {num_questions} multiple-choice questions about '{topic}' "
            f"based on the following study material. "
            "Return ONLY a valid JSON array (no markdown, no code blocks) with this exact format:\n"
            '[{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": 0, '
            '"explanation": "..."}]\n\n'
            f"Study Material:\n{context[:3000]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a quiz generation assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.8,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?\s*", "", content).strip()
                if content.endswith("```"):
                    content = content[:-3].strip()

            import json
            questions = json.loads(content)
            return questions if isinstance(questions, list) else []

        except Exception as e:
            print(f"Quiz generation error: {e}")
            return []

    def analyze_pyq_topics(self, questions_text: str) -> Dict:
        """Analyze PYQ questions to extract topics and patterns."""
        prompt = (
            "Analyze the following exam questions and provide a structured analysis. "
            "Return ONLY valid JSON (no markdown) with this exact format:\n"
            '{"topics": [{"name": "...", "count": N, "questions": [...]}], '
            '"patterns": {"define": N, "explain": N, "compare": N, "differentiate": N, "short_answer": N}, '
            '"important_topics": [...]}\n\n'
            f"Questions:\n{questions_text[:5000]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational analysis assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.5,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?\s*", "", content).strip()
                if content.endswith("```"):
                    content = content[:-3].strip()

            import json
            return json.loads(content)

        except Exception as e:
            print(f"PYQ analysis error: {e}")
            return {"topics": [], "patterns": {}, "important_topics": []}

    def explain_topic(self, topic: str) -> str:
        """Generate a simple explanation for a topic."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful tutor. Explain concepts clearly with examples."},
                    {"role": "user", "content": f"Explain '{topic}' in simple terms with examples."}
                ],
                max_tokens=512,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {str(e)}"


llm_service = LLMService()
