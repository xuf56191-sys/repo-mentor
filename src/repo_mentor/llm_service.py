"""Deepseek 大模型调用服务"""

from langchain_deepseek import ChatDeepSeek
from config import ConfigError , load_settings


def create_llm()->ChatDeepSeek:
    """创建并返回Deepseek大模型实例"""
    try:
        settings = load_settings()
    except ConfigError as error:
        print("=" * 50)
        print("配置检查失败")
        print("=" * 50)
        print(error)
        raise SystemExit(1) from error
    return  ChatDeepSeek(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=settings.model_api_key,
        # other params...
    )


def invoke_llm(llm: ChatDeepSeek, prompt:str) ->str:
    # 调用模型并返回结果
    if not prompt.strip():
        raise ValueError('prompt不能为空')

    response = llm.invoke(prompt)
    return  str(response.content)

def main():
    """连续调用两次模型，验证模型服务是否可以稳定运行。"""
    prompt = '请用一句话解释什么是AI Agent。'
    try:
        llm = create_llm()
        for index in range(1,3):
            print('=' * 30)
            print(f"第{index}次模型调用")
            print('=' * 30)
            answer = invoke_llm(llm,prompt)
            print(answer)

    except Exception as exc:
        print(f"模型调用失败：{exc}")

if __name__ =="__main__":
    main()