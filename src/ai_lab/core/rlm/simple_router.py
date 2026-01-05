"""Simple RLM Router - basic recursive inference implementation."""
import re
from typing import Optional
from .config import RLMConfig
from .adapter import InferenceClientAdapter
from ..registry import Registry
from ..inference import get_inference_client


class SimpleRLMRouter:
    """
    Simple recursive language model router.

    This implements basic RLM functionality by recursively chunking
    and processing large inputs with a smaller context model.

    Simpler than full RLM library integration, but provides the
    core functionality: handle inputs larger than context window.
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[RLMConfig] = None,
        registry: Optional[Registry] = None,
    ):
        """Initialize simple RLM router."""
        self.registry = registry or Registry()
        self.model_entry = self.registry.get(model_name)
        self.config = config or RLMConfig(model_name=model_name)

        # Get base inference client
        self.base_client = get_inference_client(self.model_entry)

        # Create adapter
        self.adapter = InferenceClientAdapter(
            client=self.base_client,
            model_name=self.model_entry.name,
        )

    def complete(
        self,
        prompt: str,
        root_prompt: Optional[str] = None,
    ) -> str:
        """
        Run RLM-style completion on potentially large context.

        Args:
            prompt: Context/document to process
            root_prompt: Task/question about the context

        Returns:
            Final answer after processing
        """
        # For small inputs, just complete directly
        if len(prompt) <= 4000:  # Safe threshold for most models
            system_prompt = (
                f"You are analyzing a document. Task: {root_prompt or 'Summarize key points'}\n\n"
                f"Document:\n{prompt}"
            )
            return self._complete_single(system_prompt)

        # For larger inputs, implement basic chunking and aggregation
        return self._complete_recursive(prompt, root_prompt or "Summarize")

    def _complete_single(self, prompt: str) -> str:
        """Single completion without chunking."""
        try:
            response = self.adapter.completion(prompt)
            # Extract just the answer part
            if isinstance(response, dict):
                return response.get("content", str(response))
            return str(response)
        except Exception as e:
            return f"Error during completion: {str(e)}"

    def _complete_recursive(self, prompt: str, task: str) -> str:
        """
        Recursive completion with chunking.

        Basic implementation:
        1. Split into chunks
        2. Process each chunk
        3. Aggregate results
        """
        # Split into manageable chunks (roughly 2000 chars each)
        chunk_size = 2000
        chunks = self._split_text(prompt, chunk_size)

        if self.config.verbose:
            print(f"[RLM] Processing {len(chunks)} chunks...")

        # Process each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            if self.config.verbose:
                print(f"[RLM] Processing chunk {i+1}/{len(chunks)}...")

            chunk_prompt = f"""
Task: {task}

Process this chunk of text:
{chunk}

Provide a brief summary focusing on the task above.
"""
            summary = self._complete_single(chunk_prompt)
            chunk_summaries.append(summary)

        # Aggregate summaries
        if len(chunk_summaries) <= 3:
            # If few chunks, just aggregate directly
            combined = "\n\n".join(chunk_summaries)
            aggregate_prompt = f"""
Task: {task}

Here are summaries from different parts of a document:
{combined}

Provide a final, consolidated answer to the task.
"""
            return self._complete_single(aggregate_prompt)
        else:
            # If many chunks, recursively aggregate
            return self._complete_recursive(
                "\n\n".join(chunk_summaries),
                task
            )

    def _split_text(self, text: str, chunk_size: int) -> list[str]:
        """
        Split text into chunks, trying to respect sentence boundaries.
        """
        chunks = []
        current = ""
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if len(current) + len(sentence) < chunk_size:
                current += " " + sentence if current else sentence
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence

        if current:
            chunks.append(current.strip())

        return chunks

    def get_usage_summary(self):
        """Get usage statistics."""
        return self.adapter.get_usage_summary()
