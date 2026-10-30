import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.AppConfig import settings

logger = logging.getLogger("heketon.agent.llm")

T = TypeVar("T", bound=BaseModel)


class LlmFactory:
    """Multi-Provider LLM Factory with Transparent Hybrid Deterministic Fallback.

    Ensures that when external API keys are missing, network is offline,
    or during fast CI/CD unit tests, the system operates deterministically.
    """

    @staticmethod
    def get_chat_model(temperature: float = 0.0) -> Any | None:
        """Returns the appropriate LangChain BaseChatModel based on available API keys."""
        # 1. Google Gemini
        if settings.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI: %s", e)

        # 2. OpenAI / OpenAI-Compatible Provider
        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                openai_kwargs: dict[str, Any] = {
                    "model": settings.OPENAI_MODEL or "gpt-4o-mini",
                    "api_key": settings.OPENAI_API_KEY,
                    "temperature": temperature,
                    "timeout": 20.0,
                    "max_retries": 1,
                }
                if settings.OPENAI_BASE_URL:
                    openai_kwargs["base_url"] = settings.OPENAI_BASE_URL

                return ChatOpenAI(**openai_kwargs)
            except Exception as e:
                logger.warning("Failed to initialize ChatOpenAI: %s", e)

        # 3. Groq
        if settings.GROQ_API_KEY:
            try:
                from langchain_groq import ChatGroq

                return ChatGroq(
                    model="llama-3.3-70b-versatile",
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning("Failed to initialize ChatGroq: %s", e)

        # 4. Anthropic
        if settings.ANTHROPIC_API_KEY:
            try:
                from langchain_anthropic import ChatAnthropic

                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    api_key=settings.ANTHROPIC_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning("Failed to initialize ChatAnthropic: %s", e)

        # 5. Ollama
        if settings.OLLAMA_BASE_URL and settings.ENVIRONMENT == "development":
            try:
                from langchain_ollama import ChatOllama

                return ChatOllama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model="llama3.2",
                    temperature=temperature,
                )
            except Exception as e:
                logger.debug("Ollama model not active or reachable: %s", e)

        return None

    @classmethod
    async def invoke_structured_or_fallback(
        cls,
        schema: type[T],
        system_instruction: str,
        user_content: str,
        fallback_fn: Callable[[], T],
        temperature: float = 0.0,
    ) -> T:
        """Invokes structured output from ChatModel; falls back to deterministic synthesizer if offline."""
        model = cls.get_chat_model(temperature=temperature)
        if model is None:
            return fallback_fn()

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            try:
                structured_llm = model.with_structured_output(schema)
                messages = [
                    SystemMessage(content=system_instruction),
                    HumanMessage(content=user_content),
                ]
                result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=12.0)
                if isinstance(result, schema):
                    return result
                if isinstance(result, dict):
                    return schema(**result)
            except Exception as tool_err:
                logger.warning(
                    "Structured tool invocation failed (%s). Falling back to direct JSON prompt...", tool_err
                )
                json_prompt = (
                    f"{system_instruction}\n\n"
                    f"IMPORTANT: Respond ONLY with a valid JSON object matching this schema:\n"
                    f"{schema.model_json_schema()}\n"
                    f"Do NOT wrap in markdown or add conversational preamble."
                )
                raw_res = await asyncio.wait_for(
                    model.ainvoke([
                        SystemMessage(content=json_prompt),
                        HumanMessage(content=user_content),
                    ]),
                    timeout=25.0,
                )
                raw_text = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
                if isinstance(raw_text, list):
                    raw_text = "".join(str(part) for part in raw_text)

                clean_text = raw_text.strip()
                if clean_text.startswith("```"):
                    lines = clean_text.split("\n")
                    clean_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                clean_text = clean_text.strip()
                return schema.model_validate_json(clean_text)

            return fallback_fn()
        except Exception as err:
            logger.info("LLM structured output invocation fell back to deterministic generator: %s", err)
            return fallback_fn()
