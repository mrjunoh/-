import streamlit as st
from custom_agents import agents
import json
from langchain_core.messages import HumanMessage

st.set_page_config(page_title="블로그 제목 생성 AI", layout="centered")

st.title("✨ AI 블로그 제목 생성기")
st. write("좌측 sidebar를 열고 api key 입력 및 원하는 제목 개수 입력 해주세요.")
st.write('sidebar에서 주의사항 및 설명을 꼭 읽어주세요. ')

# session_state에 api_key가 없으면 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "generated_titles" not in st.session_state:
    st.session_state.generated_titles = []


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

    st.markdown("---")

    on0 = st.toggle("주의사항")

    if on0:
        st.markdown("""
        '제목생성'을 시작한 후 다른 특정 요소를 건드리면 중지되는 현상이 발생합니다. 
        \n제목 생성되는 동안 해당 페이지에서 다른 버튼은 클릭하지 않으셔야합니다.
        \n추가로 해당 서비스는 완벽하지 않습니다.
        \n답변이 나오는데 30초~1분 정도가 소요된다는점 참고바랍니다.
                    """)

    on1 = st.toggle("서비스 설명")

    if on1:
        st.markdown("""
        해당 서비스는 "네이버 블로그 제목 생성 AI"입니다.
        \n
        블로그 대행사 마케튜드가 사용하는 블로그 제목 생성 기술을 AI에게 학습을 시켰습니다.
        \n
        해당 AI는 "ai agent"라는 기술을 이용해서 만들었습니다.
        \n
        ai agent를 쉽게 말하면 "ai는 목표 달성을 위해 스스로 생각하고, 여러 팀원들을 만들어줌으로 팀원들과 함께 상호작용하면서 목표 달성을 하는 방식"입니다.
        \n
        비유를 하자면 "하나의 회사"를 만들어준 것입니다.
        \n
        모든 팀원을 이끄는 대표 ai를 만들고, 각 업무를 맡길 직원 ai를 만들어서 수행되는 방식입니다.
        \n
        현재 서비스는 아주 기본적으로만 구현되어 있습니다. 
        \n
        즉 문제점이 많습니다. 답변이 출력되는 시간도 약 30초~1분 정도가 소요되며, 기술적으로 많으 부분이 딸립니다.
        \n
        현재는 제목만 있지만, 블로그 대행사 기술력이 제대로 들어간 제목, 본문 AI 서비스를 원하신다면 
        \n
        아래 설문조사에 딱 7초만 사용해주세요.
        \n
        https://docs.google.com/forms/d/e/1FAIpQLSd-boCN72ZfgeGGp9TJharRMWuObxr8wFehRmXjGKIENXyeyA/viewform?usp=dialog

        """)


    on2 = st.toggle("openAI API 발급 방법")

    if on2:
        st.markdown("""
        OpenAI(chat GPT) API key 발급방법

    1. https://platform.openai.com/docs/overview <접속

    ### 회원가입 하는 경우

    2. sign up 클릭 회원가입 하기(이미 회원이시면 뛰어넘기)
    3. 회원가입을 하고 나서 우측 상단 초록색 "Start building" 클릭하고 나머지 회원가입 진행해주기
    4. 회원가입 후 start building을 진행하시면 자연스럽게 API key 발급을 받을 수 있음.
    5. API KEY를 따로 COPY해서 저장 하기 -(후에 발급 받은 API KEY는 다시 확인 불가능 하기 때문에 따로 저장해둬야함)
    6. 다음으로 넘기면 credits 충전하는 공간이 나옴
    7. 원하는 크레딧 충전하기 -(참고로 4달동안 테스트해본 결과 5달러도 아직 다 못씀)

    ### 로그인 하는 경우

    2. 로그인 하기
    3. 우측 상단에 내 프로필 모양 클릭 후 (Your profile) 클릭
    4. 좌측 메뉴판에 "API keys" 클릭
    5. "Create new secret key" 클릭
    6. api kye의 name은 아무렇게나 적으면 됨
    -기본적으로 "My Test Key"라고 적혀있음 
    7. create secret key 클릭
    8. 클릭 후 API key가 나옴 여기서 이 API key를 우측 초록색의 "copy" 클릭 후 나만 볼 수 있는 공간에 저장해두기
    -(API 키는 한번 저장하고 다시는 확인할 수 없기 때문에 본인만 아는 공간에 따로 저장해둬야함)
    9. 복사 후 저장했으면 Done 누르기
    10. 좌측 메뉴판의 Builling 클릭
    11. 초록색 Add payment details 클릭
    12. Individual 클릭(회사면 company 클릭)
    13. 자신의 카드 등록하고 원하는 credits 충전하기 -(참고로 5달러 충전했는데 개발하면서 수많은 테스트를 했지만 다 못씀)
    """)



    on3 = st.toggle("[필독]꼭 반드시 읽어주세요.")
    if on3:
        st.markdown("""
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
        \n
        정식 오픈을 원한다면 아래 구글 설문조사에 딱 7초만 응해주시면 정말 복받을겁니다!
        \n
        https://docs.google.com/forms/d/e/1FAIpQLSd-boCN72ZfgeGGp9TJharRMWuObxr8wFehRmXjGKIENXyeyA/viewform?usp=dialog
        """)

    on4 = st.toggle("서비스 정식 오픈을 원한다면 클릭!!")
    if on4:
        st.markdown("""
        정식 오픈을 원한다면 아래 구글 설문조사에 딱 7초만 응해주시면 정말 복받을겁니다!
        \n
        https://docs.google.com/forms/d/e/1FAIpQLSd-boCN72ZfgeGGp9TJharRMWuObxr8wFehRmXjGKIENXyeyA/viewform?usp=dialog
        """)




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
                    st.subheader("생성된 제목(다른 작업 수행 시 출력 결과물이 사라집니다.)")
                    for message in final_result["messages"]:
                        if message.name == "Title_Generator":
                            try:
                                content = message.content
                                # Markdown 코드 블록 표시 제거
                                if content.startswith('```json'):
                                    content = content[7:]  # '```json ' 제거
                                if content.endswith('```'):
                                    content = content[:-3]  # '```' 제거
                                
                                # 공백 제거 후 JSON 파싱
                                content = content.strip()
                                result_dict = json.loads(content)
                                
                                # titles 추출하여 session state에 저장
                                if "titles" in result_dict:
                                    st.session_state.generated_titles = [item["title"] for item in result_dict["titles"]]
                                    # 저장된 제목들 출력
                                    for title in st.session_state.generated_titles:
                                        st.markdown(f"- {title}")
                                
                            except Exception as e:
                                st.write("처리 중 오류:", str(e))
                                st.write("원본 내용:", message.content)



                # 작업 완료 메시지
                status_area.success("✅ 모든 작업이 완료되었습니다!")

       except Exception as e:
           st.error(f"오류가 발생했습니다: {str(e)}")

# 이전에 생성된 제목이 있다면 표시
if st.session_state.generated_titles and not st.button:  # 버튼을 누르지 않은 상태에서도 결과 표시
    st.subheader("생성된 제목")
    if "titles" in result_dict:
        st.session_state.generated_titles = [item["title"] for item in result_dict["titles"]]
        # 저장된 제목들 출력
        for title in st.session_state.generated_titles:
            st.markdown(f"- {title}")

st.markdown("---")
st.caption("Made by MARKETtude")