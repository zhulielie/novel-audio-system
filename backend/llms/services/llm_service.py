import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async

from ..models import LLMModel, LLMRequest, APIKey, LLMProvider


class LLMServiceError(Exception):
    """LLM服务错误"""
    pass


class LLMService:
    """LLM服务类"""

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_api_key(self, provider: LLMProvider) -> Optional[APIKey]:
        """获取提供商的API密钥（异步版本）"""
        try:
            from django.utils import timezone

            # 获取有效的API密钥（手动过滤过期和超限的密钥）
            api_keys = await sync_to_async(list)(
                APIKey.objects.filter(
                    provider=provider,
                    is_active=True
                )
            )

            # 手动过滤未过期的密钥
            valid_api_keys = []
            for key in api_keys:
                if not key.expires_at or key.expires_at > timezone.now():
                    # 检查使用限制
                    if not key.usage_limit or key.usage_count < key.usage_limit:
                        valid_api_keys.append(key)

            api_key = valid_api_keys[0] if valid_api_keys else None

            if api_key:
                # 更新使用次数和时间
                api_key.usage_count += 1
                api_key.last_used_at = timezone.now()
                await sync_to_async(api_key.save)()

            return api_key
        except Exception as e:
            print(f"获取API密钥失败: {e}")
            return None

    def build_request_data(self, model: LLMModel, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        # SiliconFlow API 格式
        request_data = {
            "model": model.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "max_tokens": 1024  # 设置默认值
        }

        # 添加可选参数
        if 'temperature' in parameters:
            request_data['temperature'] = parameters['temperature']
        if 'max_tokens' in parameters:
            request_data['max_tokens'] = min(parameters['max_tokens'], 4096)  # 限制最大token数
        if 'top_p' in parameters:
            request_data['top_p'] = parameters['top_p']

        # 确保temperature在有效范围内
        if request_data.get('temperature', 0) < 0.01:
            request_data['temperature'] = 0.01
        elif request_data.get('temperature', 0) > 2.0:
            request_data['temperature'] = 2.0

        return request_data

    async def call_llm_api(self, provider: LLMProvider, request_data: Dict[str, Any], api_key: APIKey) -> Dict[str, Any]:
        """调用LLM API"""
        headers = {
            "Authorization": f"Bearer {api_key.api_key}",
            "Content-Type": "application/json"
        }

        # 调试信息
        print(f"发送到 {provider.name} API 的请求:")
        print(f"URL: {provider.base_url}")
        print(f"Headers: {headers}")
        print(f"Request Data: {request_data}")

        try:
            async with self.session.post(provider.base_url, json=request_data, headers=headers) as response:
                print(f"API响应状态码: {response.status}")
                response_text = await response.text()
                print(f"API响应内容: {response_text}")

                if response.status == 200:
                    return await response.json()
                else:
                    raise LLMServiceError(f"API请求失败: HTTP {response.status} - {response_text}")
        except aiohttp.ClientError as e:
            raise LLMServiceError(f"网络请求错误: {str(e)}")
        except Exception as e:
            raise LLMServiceError(f"未知错误: {str(e)}")

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应"""
        try:
            # SiliconFlow API响应格式
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                content = choice.get('message', {}).get('content', '')

                # 获取token使用情况
                usage = response_data.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                return {
                    'content': content,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': total_tokens
                }
            else:
                raise LLMServiceError("响应格式错误：缺少choices字段")
        except Exception as e:
            raise LLMServiceError(f"解析响应失败: {str(e)}")

    async def generate_response(self, model: LLMModel, prompt: str, parameters: Dict[str, Any] = None, api_key: Optional[APIKey] = None) -> Dict[str, Any]:
        """生成LLM响应"""
        if parameters is None:
            parameters = {}

        # 设置默认参数
        default_params = {
            'temperature': 0.7,
            'max_tokens': min(model.max_tokens, 1000),  # 限制最大token数
            'top_p': 1.0
        }
        parameters = {**default_params, **parameters}

        # 获取API密钥（异步）
        if not api_key:
            api_key = await self.get_api_key(model.provider)
        if not api_key:
            raise LLMServiceError(f"未找到有效的API密钥用于提供商: {model.provider.name}")

        # 构建请求数据
        request_data = self.build_request_data(model, prompt, parameters)

        # 调用API
        response_data = await self.call_llm_api(model.provider, request_data, api_key)

        # 解析响应
        result = self.parse_response(response_data)

        return result

    async def process_llm_request(self, llm_request: LLMRequest) -> None:
        """处理LLM请求"""
        start_time = time.time()

        try:
            # 更新请求状态为处理中
            llm_request.status = 'processing'
            await sync_to_async(llm_request.save)()

            # 生成响应（使用已有的API密钥）
            result = await self.generate_response(
                llm_request.model,
                llm_request.prompt,
                llm_request.parameters,
                llm_request.api_key
            )

            # 更新请求结果
            llm_request.response = result['content']
            llm_request.input_tokens = result['input_tokens']
            llm_request.output_tokens = result['output_tokens']
            llm_request.total_tokens = result['total_tokens']
            llm_request.processing_time = time.time() - start_time
            llm_request.status = 'completed'

            # 计算成本（如果有价格信息）
            if llm_request.model.cost_per_1k_input and llm_request.model.cost_per_1k_output:
                input_cost = (llm_request.input_tokens / 1000) * float(llm_request.model.cost_per_1k_input)
                output_cost = (llm_request.output_tokens / 1000) * float(llm_request.model.cost_per_1k_output)
                llm_request.cost = input_cost + output_cost

            await sync_to_async(llm_request.save)()

        except Exception as e:
            # 处理错误
            llm_request.status = 'failed'
            llm_request.error_message = str(e)
            llm_request.processing_time = time.time() - start_time
            await sync_to_async(llm_request.save)()
            raise


async def generate_llm_response(model: LLMModel, prompt: str, parameters: Dict[str, Any] = None, api_key: Optional[APIKey] = None) -> Dict[str, Any]:
    """便捷函数：生成LLM响应"""
    async with LLMService() as service:
        return await service.generate_response(model, prompt, parameters, api_key)


async def process_llm_request_async(llm_request: LLMRequest) -> None:
    """异步处理LLM请求"""
    async with LLMService() as service:
        await service.process_llm_request(llm_request)
