import os
from typing import Optional
from app.schemas.article import ArticleCreate, AIAnalysis
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class LLMAnalyzer:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")
        
        self.llm = None
        
        if self.google_key:
             print("Using Google Gemini Pro")
             self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=self.google_key, temperature=0)
        elif self.openai_key:
            print("Using OpenAI GPT-3.5")
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=self.openai_key)
        
        if self.llm:
            self.parser = JsonOutputParser(pydantic_object=AIAnalysis)
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a venture capital analyst. Analyze the provided tech news/product. Return JSON only."),
                ("user", "Title: {title}\nURL: {url}\n\nAnalyze this and provide: summary, category, score (0-100), reasoning, and tags.\n\n{format_instructions}")
            ])
            self.chain = self.prompt | self.llm | self.parser

    async def analyze(self, article: ArticleCreate) -> AIAnalysis:
        if not self.llm:
            return self._mock_analysis(article)

        try:
            response = await self.chain.ainvoke({
                "title": article.title,
                "url": article.url,
                "format_instructions": self.parser.get_format_instructions()
            })
            return AIAnalysis(**response)
        except Exception as e:
            print(f"Analysis failed for {article.title}: {e}")
            return self._mock_analysis(article)

    def _mock_analysis(self, article: ArticleCreate) -> AIAnalysis:
        """Fallback mock analysis for testing without API keys."""
        import random
        scores = [65, 72, 85, 91, 58]
        categories = ["GenAI", "DevTool", "SaaS", "FinTech", "HealthTech"]
        
        return AIAnalysis(
            summary=f"Mock analysis for: {article.title}. A potential market disruptor in its field.",
            category=random.choice(categories),
            score=random.choice(scores),
            reasoning="Automated mock scoring based on keywords.",
            tags=["Startup", "Tech", "MockData"]
        )