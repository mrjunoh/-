import warnings
warnings.filterwarnings('ignore')

from langchain_core.tools import tool

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from selenium.webdriver.common.keys import Keys

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from pydantic import BaseModel
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import create_react_agent
from typing import Sequence, TypedDict, Annotated
import functools
import operator


from typing import List, Dict
import json
import os

import requests
from bs4 import BeautifulSoup


def agents(keyword:str, num_titles:int, api_key:str ):
    os.environ['OPENAI_API_KEY'] = api_key


    @tool
    def search_tool(keyword:str) -> list[str]:
        """
        사용자 요청 키워드로 검색 후 상위 6개 제목 반환
        keyword: search keyword
        retrun: 상위 6개 제목 return
        """

        print("-- 제목 수집 실행됨 -- ")
        search_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={keyword}"
        
        # HTTP GET 요청으로 HTML 가져오기
        response = requests.get(search_url)
        
        # 요청 성공 확인
        if response.status_code == 200:  # HTTP 상태 코드 200은 성공을 의미
            html_content = response.text  # HTML 소스 코드 저장
            soup = BeautifulSoup(html_content, "html.parser")  # BeautifulSoup으로 파싱

            # a 태그 찾기
            title_links = soup.find_all("a", attrs={"class": "title_link"})
            
            # 텍스트 추출
            titles = [link.get_text(strip=True) for link in title_links]  # 각 링크에서 텍스트 추출
            # 결과 출력
            for i, title in enumerate(titles[:6], 1):
                print(f"{i}. {title}")
            return titles[:6]
        else:
            print(f"HTTP 요청 실패: 상태 코드 {response.status_code}")
            return []

    def initialize_driver():
        chromedriver_autoinstaller.install()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


        service = Service()  # 명시적으로 Service 객체 생성
        return webdriver.Chrome(service=service, options=chrome_options)

    # 검색창에 키워드 입력
    @tool
    def auto_search_keyword(keyword: str) -> list:
        """
        해당 함수는 크롤링을 통해 사용자의 키워드를 검색창에 입력 후 상위노출 제목을 작성하기 위해 '자동완성 키워드'를 가져오는 기능.
        """

        print("-- 자동완성 키워드 수집 실행됨 --")
        def get_max_li_index(driver):
            """
            해당 함수는 auto_search_keyword를 수행할 때 '자동완성 키워드'의 최대값을 구하는 함수
            """
            # 페이지 로드 대기
            wait = WebDriverWait(driver, 10)
            li_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[2]/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/div[1]/ul/li")))
            return len(li_elements)

        driver = initialize_driver()
        url = "https://www.naver.com/"
        driver.get(url)

        auto_keyword = []

        try:
            # 검색창의 XPath
            xpath = "/html/body/div[2]/div[1]/div/div[3]/div/div/form/fieldset/div/input"

            # 검색창 요소 찾기
            wait = WebDriverWait(driver, 10)  # 최대 10초 대기
            search_box = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

            # 검색창에 키워드 입력
            search_box.clear()  # 기존 내용 제거
            search_box.send_keys(keyword)  # 키워드 입력
            print(f"'{keyword}' 키워드를 검색창에 입력했습니다.")

            # 자동완성 첫 번째 키워드 XPath 확인
            first_xpath = "/html/body/div[2]/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/div[1]/ul/li[1]/a/span/span[2]"
            try:
                wait = WebDriverWait(driver, 10)  # 최대 10초 대기
                wait.until(EC.presence_of_element_located((By.XPATH, first_xpath)))
                print("자동완성 키워드가 표시됩니다. 키워드 추출을 시작합니다.")
            except Exception:
                print("자동완성 키워드가 없습니다. 종료합니다.")
                return []

            max_li_index = get_max_li_index(driver)

            for idx in range(1, max_li_index+1):
                xpaths = f"/html/body/div[2]/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/div[1]/ul/li[{idx}]/a/span/span[2]"
                try:
                    wait = WebDriverWait(driver, 10)  # 최대 10초 대기
                    element = wait.until(EC.presence_of_element_located((By.XPATH, xpaths)))
                    if element:
                        # 제목 텍스트 추출
                        keyword = element.text
                        auto_keyword.append(keyword)
                        print(f"{idx}번째 -> keyword: {keyword}")
                except Exception as e:
                    print(f"자완 키워드 추출 에러: {e}")
            # search_box.send_keys(Keys.RETURN)  # 엔터 키 입력
            return auto_keyword
        except Exception as e:
            print(f"키워드 입력 중 오류 발생: {e}")
        finally:
            driver.quit()




    # 1. 멤버 정의
    # 멤버: 1. 타이틀 가져오기 2. 타이틀 공통단어 추출 3. 자완 키워드 추출  4. 제목 생성
    members = ["Title_Searcher", "Keyword_Extractor", "AutoComplete_Searcher", "Title_Generator"]

    # 2. 시스템 프롬프트 정의
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers: {members}. Your task is to coordinate the process of:"
        " 1) Title_Searcher - Execute ONCE to get titles"
        " 2) Keyword_Extractor - Analyze the titles from step 1"
        " 3) AutoComplete_Searcher - Execute ONCE to get suggestions"
        " 4) Title_Generator - Create final titles"
        " Title_Searcher and AutoComplete_Searcher MUST be executed exactly once."
        " Title_Searcher and AutoComplete_Searcher  Never call them again after their first execution."
        " When finished, respond with FINISH."
    )


    # 3. 옵션 정의
    options = ["FINISH"] + members

    # 4. 응답 모델 정의
    class routeResponse(BaseModel):
        next: Literal[*options]

    # 5. 프롬프트 템플릿 정의
    #supervision에게 다음 작업을 수행하도록 어떤 작업을 할건지 정확하고 철저하게 알려주고 있음
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}"
                "\nOrder of operations:"
                "\n1. Title_Searcher MUST BE EXECUTED EXACTLY ONCE to get titles"
                "\n2. Keyword_Extractor to analyze titles (can be called multiple times if needed)"
                "\n3. AutoComplete_Searcher MUST BE EXECUTED EXACTLY ONCE to get suggestions"
                "\n4. Title_Generator to create final titles (can be called multiple times if needed)"
                "\nNEVER call Title_Searcher or AutoComplete_Searcher more than once."
                "\nFINISH when all steps are complete."
                "\nIMPORTANT: Check the conversation history - if Title_Searcher or AutoComplete_Searcher"
                " have already been executed once, NEVER call them again."
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    # 6. LLM 초기화
    llm_supervision = ChatOpenAI(model='gpt-4o',temperature=0)
    llm = ChatOpenAI(model='gpt-4o')
    llm_tool = ChatOpenAI(model='gpt-4o-mini',temperature=0)
    llm_tool_search = ChatOpenAI(model='gpt-3.5-turbo',temperature=0)

    # 7. Supervisor 함수 정의
    def supervisor_agent(state):
        supervisor_chain = (
            prompt
            | llm_supervision.with_structured_output(routeResponse)
        )
        return supervisor_chain.invoke(state)



    # 1. 상태 타입 정의
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]
        next: str  # supervisor가 정하는 next값

    # 2. 에이전트 노드 함수 정의
    def agent_node(state, agent, name):
        result = agent.invoke(state)
        return {"messages": [HumanMessage(content=result["messages"][-1].content, name=name)]}


    # 3. Title Searcher 에이전트 생성
    title_searcher_prompt = """You are a title search specialist who uses Naver search to find relevant titles.
Your task is to search for titles related to the given keyword and return the results.
IMPORTANT: You must execute the search_tool EXACTLY ONCE and return the results immediately.
Do not attempt multiple searches or refinements.
Always use the search_tool for getting titles from Naver, and return the results from that single execution.
"""
    title_searcher = create_react_agent(
        llm_tool_search,
        tools=[search_tool],  # 앞서 정의한 custom tool
        state_modifier=title_searcher_prompt
    )
    title_searcher_node = functools.partial(agent_node, agent=title_searcher, name="Title_Searcher")


    # 4. Keyword Extractor 에이전트 생성
    keyword_extractor_prompt = """You are an expert keyword extraction specialist for SEO optimization.

    MAIN TASKS:
    1. Analyze provided Korean titles
    2. Extract key patterns and important terms
    3. Evaluate keyword significance (1-10 scale)
    4. Consider SEO impact and search intent

    ANALYSIS METHOD:
    1. Identify:
    - Common phrases across titles
    - Unique but important terms
    - Trending expressions
    - Question patterns or problem-solving terms

    2. Classify Keywords:
    - Core Keywords (8-10): Main topic terms
    - Supporting Keywords (5-7): Related important terms
    - Context Keywords (1-4): Supplementary terms

    OUTPUT FORMAT:
    {
        "keywords": [
            {
                "word": "string",
                "importance": number(1-10),
                "type": "core|supporting|context",
                "reason": "Brief explanation"
            }
        ],
        "summary": "Brief analysis overview"
    }

    Remember: Focus on Korean language nuances and current trends. Your analysis will directly impact final title generation."""


    keyword_extractor = create_react_agent(
        llm,
        tools=[],  # 이 에이전트는 특별한 tool 없이 LLM의 분석 능력만 사용
        state_modifier=keyword_extractor_prompt
    )
    keyword_extractor_node = functools.partial(agent_node, agent=keyword_extractor, name="Keyword_Extractor")


    # 5. AutoComplete Searcher 에이전트 생성
    auto_complete_prompt = """You are an auto-complete keyword specialist for Korean search optimization.

YOUR CORE TASK:
Get auto-complete suggestions for the given keyword from Naver using the auto_search_keyword tool.

SEARCH STRATEGY:
1. First try with the full original keyword
2. If no auto-complete results found, identify and use the MAIN KEYWORD:
  - For compound keywords, focus on the main subject/topic
  - Avoid searching generic terms that dilute the core meaning

WORKFLOW:
1. Try the original full keyword first
2. If no results:
  - Identify the main keyword (core topic)
  - Search using the main keyword only
  - Avoid searching generic/auxiliary terms

OUTPUT FORMAT:
Always return the results in an organized list, indicating which keyword was used for each suggestion.

EXAMPLES:
1. Input: "부가세 세무사" (no results)
  - Main keyword: "세무사" (core profession)
  - Search for: "세무사"
  - Avoid: searching "부가세" separately as it's a subtopic

2. Input: "파이썬 공부" (no results)
  - Main keyword: "파이썬" (core subject)
  - Search for: "파이썬"
  - Avoid: searching "공부" separately as it's a generic term

3. Input: "주식투자 초보" (no results)
  - Main keyword: "주식투자" (core topic)
  - Search for: "주식투자"
  - Avoid: searching "초보" separately as it's a descriptor

Remember: 
- Focus on the main subject/topic
- Avoid diluting results with generic terms
- The goal is to get relevant suggestions that maintain focus on the core topic"""



    auto_complete_searcher = create_react_agent(
        llm_tool,
        tools=[auto_search_keyword],  # 앞서 정의한 custom tool
        state_modifier=auto_complete_prompt
    )
    auto_complete_node = functools.partial(agent_node, agent=auto_complete_searcher, name="AutoComplete_Searcher")



    # 6. Title Generator 에이전트 생성
    title_generator_prompt = """You are a master title optimization expert for Korean content.

    CORE OBJECTIVE:
    Create highly engaging and SEO-optimized titles by harmoniously combining:
    1. Original user search keyword
    2. Common keywords from top-ranking titles
    3. Auto-complete suggestions

    TITLE CREATION RULES:
    1. MUST Incorporate:
    - User's original keyword (highest priority)
    - At least 1-2 high-importance keywords from analysis
    - 1 trending auto-complete keyword when relevant

    2. Optimization Guidelines:
    - Length: 15-35 characters (optimal for Korean SEO)
    - Structure: [Attention Grabber] + [Core Keyword] + [Benefit/Promise]
    - Include numbers or specific data when applicable
    - Use curiosity gaps or emotional triggers

    3. Quality Checks:
    - Natural flow in Korean language
    - Clear value proposition
    - Search intent alignment
    - Click-worthy without clickbait

    OUTPUT FORMAT:
    {
        "titles": [
            {
                "title": "string",
                "keywords_used": ["list of incorporated keywords"],
                "ranking_confidence": number(1-10)
            }
        ],
        "reasoning": "Brief explanation of title creation strategy"
    }"""

    title_generator = create_react_agent(
        llm,
        tools=[],  # 이 에이전트는 특별한 tool 없이 LLM의 생성 능력만 사용
        state_modifier=title_generator_prompt
    )
    title_generator_node = functools.partial(agent_node, agent=title_generator, name="Title_Generator")


    ###########################
    #그래프 생성

    # 7. 워크플로우 그래프 생성
    workflow = StateGraph(AgentState)

    # 8. 노드 추가
    workflow.add_node("Title_Searcher", title_searcher_node)
    workflow.add_node("Keyword_Extractor", keyword_extractor_node)
    workflow.add_node("AutoComplete_Searcher", auto_complete_node)
    workflow.add_node("Title_Generator", title_generator_node)
    workflow.add_node("supervisor", supervisor_agent)


    # 1. 멤버들에 대한 edge 추가
    #각 엣지들은 supervisor에 붙여야 하니까
    for member in members:
        workflow.add_edge(member, "supervisor")

    # 2. 조건부 매핑 설정
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END

    # 3. supervisor의 조건부 edge 추가
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        conditional_map
    )

    # 4. 시작점 설정
    workflow.add_edge(START, "supervisor")

    # 5. 그래프 컴파일
    return workflow.compile()
#workflow.compile(max_iterations=1)

    # #종 결과만 보기
    # print("\n=== 최종 결과 ===")
    # print(f"keyword:{keyword}\nnumtitles:{num_titles}")
    # final_result = graph.invoke({
    #     "messages": [
    #         HumanMessage(content=f"블로그에 쓸 '{keyword}' 관련 제목을 {num_titles}개 생성해주세요.")
    #     ]
    # })

    # # Title_Generator의 최종 출력에서 제목만 추출하여 세로로 출력
    # result = []
    # for message in final_result["messages"]:
    #     if message.name == "Title_Generator":
    #         import json
    #         result_dict = json.loads(message.content)
    #         # print("\n결과:")
    #         for item in result_dict["titles"]:
    #             print(f"- {item['title']}")
    #             result.append(item['title'])
    
    # return result

# if __name__ == "__main__":
#     api_key = "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"
#     agent = agents("블로그",2,api_key)

#     print(agent)