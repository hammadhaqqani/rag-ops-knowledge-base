"""AWS Bedrock LLM integration for response generation."""

import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockLLM:
    """Generate text using AWS Bedrock LLM models."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-v2",
        region: str = "us-east-1",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Initialize Bedrock LLM client.

        Args:
            model_id: Bedrock model ID
            region: AWS region
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.model_id = model_id
        self.region = region
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        try:
            if "claude" in self.model_id.lower():
                return await self._generate_claude(prompt, system_prompt)
            else:
                # Generic format for other models
                return await self._generate_generic(prompt, system_prompt)

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            raise

    async def _generate_claude(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Claude model."""
        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "user",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }

        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())

        # Extract text from Claude response
        if "content" in response_body and len(response_body["content"]) > 0:
            return response_body["content"][0].get("text", "")
        else:
            raise ValueError("Unexpected response format from Claude")

    async def _generate_generic(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using generic model format."""
        body = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if system_prompt:
            body["system"] = system_prompt

        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())

        # Try common response fields
        if "completion" in response_body:
            return response_body["completion"]
        elif "text" in response_body:
            return response_body["text"]
        elif "generated_text" in response_body:
            return response_body["generated_text"]
        else:
            raise ValueError(f"Unexpected response format from {self.model_id}")

    async def check_availability(self) -> bool:
        """Check if Bedrock model is available."""
        try:
            # Try to list foundation models to verify access
            bedrock_client = boto3.client("bedrock", region_name=self.region)
            response = bedrock_client.list_foundation_models()

            # Check if our model is in the list
            model_ids = [
                model["modelId"] for model in response.get("modelSummaries", [])
            ]
            return self.model_id in model_ids

        except Exception as e:
            logger.warning(f"Could not verify Bedrock availability: {e}")
            # Return True as a fallback - actual errors will surface during generation
            return True
