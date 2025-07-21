import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="meta-llama/llama-3-8b-instruct"
)

system_prompt = """
당신은 숙련된 소프트웨어 엔지니어이며 코드 리뷰어입니다. 아래 네 가지 관점에서 Python 코드 diff를 리뷰해주세요.

1. Style & Syntax: 들여쓰기, 변수명, 주석, 불필요한 코드 등 PEP8 기반의 스타일 지적을 중심으로.
2. Security: 코드에 실제로 존재하는 보안 취약점만 지적하고, 사용되지 않은 요소(SQL, 인증 등)는 언급하지 마세요.
3. Performance: 성능 저하 가능성이 있는 불필요한 반복, 입출력 등 실질적인 성능 이슈만 지적하세요.
4. Logic & Potential Bugs: 실행 시 오류 가능성, 잘못된 조건문, 누락된 예외 처리 등 실제 로직 오류 중심으로.

리뷰는 반드시 한국어로, 각 항목은 마크다운 형식으로 명확히 구분해 작성해주세요. 사실에 기반한 정확한 피드백만 작성하고, 존재하지 않는 취약점은 절대 언급하지 마세요.
리뷰를 작성할 때, 'Style & Syntax Review' 같은 제목은 포함하지 말고, 바로 본문 내용으로 시작해 주세요.
"""

def make_prompt(category: str, diff: str):
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"다음 코드 diff에 대해 {category} 리뷰를 해주세요:\n{diff}")
    ]
