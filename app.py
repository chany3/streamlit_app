import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="실시간 항공권 최저가 검색", layout="wide")

st.title("✈️ 실시간 항공권 최저가 검색기")
st.write("스트림릿 클라우드에서 동작하는 실시간 대시보드입니다.")

# --- 1. 사이드바: 검색 조건 및 필터링 ---
st.sidebar.header("검색 조건 설정")

# 지역 선택 (특정 공항 코드 또는 범위 지정 가능)
origin = st.sidebar.text_input("출발지 (예: ICN, 서울)", value="ICN")
destination = st.sidebar.text_input("도착지 (예: NRT, 서유럽)", value="NRT")

# 경유 횟수 선택
stops_option = st.sidebar.radio(
    "경유 횟수", 
    ["직항", "1회 경유", "2회 이상 경유"]
)

# 필터링 기능 (가격대, 대기 시간)
st.sidebar.subheader("필터링")
max_price = st.sidebar.slider("최대 예산 (만원)", min_value=10, max_value=300, value=150, step=5)
max_layover = st.sidebar.slider("최대 경유 대기 시간 (시간)", min_value=0, max_value=24, value=12, step=1)

# 자동 업데이트 토글
auto_refresh = st.sidebar.toggle("10초 자동 업데이트 켜기", value=False)

# --- 2. 가상 API 데이터 생성 함수 ---
def fetch_flight_data(origin, dest, stops, price_limit, layover_limit):
    """실제 API(Amadeus 등) 호출을 대체하는 가상 데이터 생성 함수"""
    airlines = ["대한항공", "아시아나", "제주항공", "진에어", "루프트한자", "에미레이트"]
    
    data = []
    # 검색 조건에 맞는 가짜 데이터 5~15개 생성
    for _ in range(random.randint(5, 15)):
        price = random.randint(10, 300)
        layover = random.randint(0, 24) if stops != "직항" else 0
        
        # 필터링 조건 적용
        if price <= price_limit and layover <= layover_limit:
            data.append({
                "항공사": random.choice(airlines),
                "출발지": origin.upper(),
                "도착지": dest.upper(),
                "경유 횟수": stops,
                "경유 대기 시간(시간)": layover if stops != "직항" else "-",
                "가격(만원)": price,
                "업데이트 시간": datetime.now().strftime("%H:%M:%S")
            })
            
    # 가격순으로 정렬
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by="가격(만원)").reset_index(drop=True)
    return df

# --- 3. 메인 화면 구성 및 업데이트 로직 ---
# 데이터를 표시할 빈 공간(placeholder) 생성
data_placeholder = st.empty()

# 현재 설정된 필터 조건으로 데이터 로드
current_data = fetch_flight_data(origin, destination, stops_option, max_price, max_layover)

with data_placeholder.container():
    if current_data.empty:
        st.warning("조건에 맞는 항공권이 없습니다. 필터를 조정해 보세요.")
    else:
        st.success(f"최저가: {current_data['가격(만원)'].iloc[0]}만원 (업데이트: {datetime.now().strftime('%H:%M:%S')})")
        st.dataframe(current_data, use_container_width=True)

# 10초 자동 업데이트 로직
if auto_refresh:
    time.sleep(10)
    st.rerun() # 스트림릿 스크립트를 처음부터 다시 실행하여 데이터 갱신
