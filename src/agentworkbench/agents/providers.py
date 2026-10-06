import os
import json
import uuid
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers supplying decision choices to the agent tool loop."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes conversation message history and available tool definitions.
        Returns a dict:
            {"type": "tool_call", "tool_call_id": "...", "tool_name": "...", "arguments": {...}, "raw_message": {...}}
        OR
            {"type": "finish", "content": "..."}
        """
        pass


class GroqProvider(BaseLLMProvider):
    """
    Provider adapter for Groq cloud inference via OpenAI-compatible tool-calling API.
    Uses free GROQ_API_KEY without paid dependencies.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    def generate(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return {"type": "error", "error": "GROQ_API_KEY environment variable is not set."}

        formatted_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {"type": "object", "properties": {}})
                }
            }
            for t in tools
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": formatted_tools,
            "tool_choice": "auto",
            "temperature": 0.0,
            "max_tokens": 800
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        request_json = json.dumps(payload)
        messages_json = json.dumps(messages)
        tools_json = json.dumps(formatted_tools)
        print(
            f"[Groq] messages={len(messages)} "
            f"tools={len(formatted_tools)} "
            f"request_chars={len(request_json)} "
            f"message_chars={len(messages_json)} "
            f"tool_chars={len(tools_json)}"
        )
        req = urllib.request.Request(
            url,
            data=request_json.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "AgentWorkBench/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                choice_msg = res_data["choices"][0]["message"]
                
                tool_calls = choice_msg.get("tool_calls")
                if tool_calls and len(tool_calls) > 0:
                    tc = tool_calls[0]
                    tc_id = tc.get("id", f"call_{uuid.uuid4().hex[:8]}")
                    func = tc["function"]
                    t_name = func["name"]
                    t_args = json.loads(func.get("arguments", "{}"))
                    
                    if t_name == "finish":
                        return {"type": "finish", "content": t_args.get("reason", "Task finished")}
                    
                    return {
                        "type": "tool_call",
                        "tool_call_id": tc_id,
                        "tool_name": t_name,
                        "arguments": t_args,
                        "raw_message": choice_msg
                    }

                content = choice_msg.get("content", "")
                return {"type": "finish", "content": content}

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            return {"type": "error", "error": f"Groq API HTTP Error {e.code}: {err_body}"}
        except Exception as e:
            return {"type": "error", "error": f"Groq API error: {str(e)}"}


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM Provider for offline testing of multi-step tool-calling agent loops.
    No API keys or network requests required.
    """

    def __init__(self, response_sequence: Optional[List[Dict[str, Any]]] = None):
        self.response_sequence = response_sequence or []
        self.call_count = 0

    def generate(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.call_count < len(self.response_sequence):
            res = self.response_sequence[self.call_count]
            self.call_count += 1
            # Auto-assign tool_call_id if missing
            if res.get("type") == "tool_call" and "tool_call_id" not in res:
                res["tool_call_id"] = f"mock_call_{self.call_count}"
            return res
        
        last_msg = messages[-1] if messages else {}
        content_str = str(last_msg.get("content", ""))
        self.call_count += 1
        
        if "ticket" in content_str.lower() and self.call_count == 1:
            return {
                "type": "tool_call",
                "tool_call_id": f"mock_call_{self.call_count}",
                "tool_name": "get_ticket",
                "arguments": {"ticket_id": "tck-101"}
            }
        
        return {"type": "finish", "content": "Default mock response"}
