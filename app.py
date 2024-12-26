import streamlit as st
from custom_agents import agents
import json
from langchain_core.messages import HumanMessage

st.title("✨ AI 블로그 제목 생성기")

# session_state에 api_key가 없으면 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""


# 사이드바에 설정 옵션 배치
with st.sidebar:
    st.header("🛠 설정")
    # API 키 입력 (session_state 활용)
    api_key_input = st.text_input(
        "OpenAI API Key", 
        type="password",
        value=st.session_state.api_key  # 저장된 값 불러오기
    )
    
    # API 키가 변경되면 session_state 업데이트
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
    # 생성할 제목 개수 선택
    num_titles = st.number_input("생성할 제목 개수", min_value=1, max_value=10, value=5)

# 메인 화면
keyword = st.text_input("키워드를 입력하세요", placeholder="예: 코딩 잘하는 방법")


if st.button("제목 생성하기", type="primary"):
   if not st.session_state.api_key:
       st.error("API 키를 입력해주세요!")
   elif not keyword:
       st.error("키워드를 입력해주세요!")
   else:
       try:
            
            with st.spinner("제목을 생성하고 있습니다..."):
                status_area = st.empty()
                result_area = st.container()  # 결과를 표시할 영역
                
                graph = agents(keyword=keyword, num_titles=num_titles, api_key=st.session_state.api_key)
                
                # 진행상황 표시를 위한 stream
                for s in graph.stream({
                    "messages": [
                        HumanMessage(content=f"블로그에 쓸 '{keyword}' 관련 제목을 {num_titles}개 생성해주세요.")
                    ]
                }):
                    if "__end__" not in s:
                        if "Title_Searcher" in str(s):
                            status_area.info("🔍 키워드 관련 제목을 검색 중입니다...")
                        elif "Keyword_Extractor" in str(s):
                            status_area.info("📝 검색된 제목에서 키워드를 추출하고 있습니다...")
                        elif "AutoComplete_Searcher" in str(s):
                            status_area.info("🔎 제목 생성을 위한 추가 정보를 수집하고 있습니다...")
                        elif "Title_Generator" in str(s):
                            status_area.info("✨ 최적화된 제목을 생성하고 있습니다...")

                # 최종 결과 가져오기 (별도의 invoke 호출)
                final_result = graph.invoke({
                    "messages": [
                        HumanMessage(content=f"블로그에 쓸 '{keyword}' 관련 제목을 {num_titles}개 생성해주세요.")
                    ]
                })


                print("제목 생성 완료")
                # 결과 출력
                with result_area:
                    st.subheader("생성된 제목")
                    for message in final_result["messages"]:
                        if message.name == "Title_Generator":
                            try:
                                # 마크다운 코드 블록 표시 제거
                                content = message.content
                                if content.startswith('```json'):
                                    content = content.replace('```json', '', 1)
                                if content.endswith('```'):
                                    content = content[:-3]
                                
                                # JSON 파싱
                                result_dict = json.loads(content.strip())
                                for item in result_dict["titles"]:
                                    st.markdown(f"- {item['title']}")
                            except json.JSONDecodeError as e:
                                st.error(f"JSON 파싱 오류: {str(e)}")
                                st.write("파싱 실패한 내용:", message.content)
                            except Exception as e:
                                st.error(f"기타 오류: {str(e)}")

                # 작업 완료 메시지
                status_area.success("✅ 모든 작업이 완료되었습니다!")

       except Exception as e:
           st.error(f"오류가 발생했습니다: {str(e)}")



# from google.oauth2.service_account import Credentials
# import gspread

# on = st.toggle("해당 서비스 설명[필참]")




on = st.toggle("[필독]꼭 반드시 읽어주세요.")
if on:
    text="""
    반갑습니다. 블로그 대행사 마케튜드입니다.
    \n
    사람들이 블로그 대행사에 맡기는 이유는 2가지라 생각합니다.
    \n
    1. 최적화 노출을 위해서
    \n
    2. 마케팅적 글쓰기를 위해서
    \n
    하지만 마케팅 대행사에 맡기기에는 월에 최소 몇백만원이 깨지게 됩니다.
    \n
    그래서 저희는 저희가 가지고 있는 블로그, 마케팅적 기술들을 AI 서비스로 만들 생각입니다.
    \n
    혹시 정식 서비스 오픈을 원하신다면 아래 버튼 체크 및 이메일 주소 입력만 해주시면 되겠습니다.
    \n
    서비스가 오픈되면 이메일 주소로 누구보다 빠르게 알려드리겠습니다.
    \n
    감사합니다.
    """
    st.write(text)