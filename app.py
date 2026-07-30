import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime, timezone, timedelta

# --- 한국 시간 설정 (UTC+9) ---
KST = timezone(timedelta(hours=9))

# --- 한글 초성 자동 추출 함수 ---
def get_choseong(text):
    """한글 문자열에서 초성만 추출하여 자동 반환하는 함수"""
    choseong_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    result = ""
    for char in text:
        # 문자가 한글 '가' ~ '힣' 사이인 경우만 초성 변환
        if '가' <= char <= '힣':
            index = (ord(char) - ord('가')) // 588
            result += choseong_list[index]
        else:
            result += char
    return result

# --- 공항/지역 데이터 준비 ---
# 여기에 공항 코드와 한글 이름만 추가하면 코드가 알아서 초성을 만들어줍니다.
# --- 공항/지역 데이터 준비 (약 150개 주요 공항) ---
airport_data = {
    # 한국
    "ICN": "인천", "GMP": "김포", "CJU": "제주", "PUS": "부산/김해", 
    "TAE": "대구", "CJJ": "청주", "KWJ": "광주", "USN": "울산", 
    "KUV": "군산", "WJU": "원주", "YNY": "양양", "RSU": "여수", "HIN": "사천",

    # 아시아 - 일본
    "NRT": "도쿄/나리타", "HND": "도쿄/하네다", "KIX": "오사카/간사이", "ITM": "오사카/이타미", 
    "NGO": "나고야", "FUK": "후쿠오카", "CTS": "삿포로", "OKA": "오키나와", 
    "KOJ": "가고시마", "FSZ": "시즈오카", "SDJ": "센다이", "HIJ": "히로시마", 
    "KMJ": "구마모토", "NGS": "나가사키", "OIT": "오이타",

    # 아시아 - 중화권
    "PEK": "베이징/서우두", "PKX": "베이징/다싱", "PVG": "상하이/푸둥", "SHA": "상하이/훙차오", 
    "CAN": "광저우", "SZX": "선전", "CTU": "청두", "CKG": "충칭", "XIY": "시안", 
    "HGH": "항저우", "XMN": "샤먼", "DLC": "다롄", "TAO": "칭다오", 
    "HKG": "홍콩", "MFM": "마카오", "TPE": "타이베이/타오위안", "TSA": "타이베이/송산", 
    "KHH": "가오슝", "RMQ": "타이중",

    # 아시아 - 동남아/기타
    "BKK": "방콕/수완나품", "DMK": "방콕/돈므앙", "HKT": "푸껫", "CNX": "치앙마이", 
    "SIN": "싱가포르", "KUL": "쿠알라룸푸르", "PEN": "페낭", "BKI": "코타키나발루", 
    "CGK": "자카르타", "DPS": "발리", "SGN": "호찌민", "HAN": "하노이", 
    "DAD": "다낭", "CXR": "냐짱", "PQC": "푸꾸옥", "MNL": "마닐라", 
    "CEB": "세부", "CRK": "클라크", "RGN": "양곤", "VTE": "비엔티안", 
    "PNH": "프놈펜", "REP": "씨엠립", "DEL": "델리", "BOM": "뭄바이",

    # 미주 - 북미
    "JFK": "뉴욕/JFK", "EWR": "뉴욕/뉴어크", "LGA": "뉴욕/라과디아", "LAX": "로스앤젤레스", 
    "SFO": "샌프란시스코", "ORD": "시카고", "ATL": "애틀랜타", "DFW": "댈러스", 
    "DEN": "덴버", "SEA": "시애틀", "LAS": "라스베이거스", "MCO": "올랜도", 
    "MIA": "마이애미", "BOS": "보스턴", "IAD": "워싱턴/덜레스", "DCA": "워싱턴/내셔널", 
    "YVR": "밴쿠버", "YYZ": "토론토", "YUL": "몬트리올", "YYC": "캘거리", 
    "HNL": "호놀룰루", "GUM": "괌", "SPN": "사이판",

    # 미주 - 중남미
    "GRU": "상파울루", "GIG": "리우데자네이루", "EZE": "부에노스아이레스/에세이사", 
    "AEP": "부에노스아이레스/호르헤뉴베리", "SCL": "산티아고", "BOG": "보고타", 
    "LIM": "리마", "MEX": "멕시코시티", "CUN": "칸쿤", "HAV": "아바나",

    # 유럽
    "LHR": "런던/히스로", "LGW": "런던/개트윅", "CDG": "파리/샤를드골", "ORY": "파리/오를리", 
    "FRA": "프랑크푸르트", "MUC": "뮌헨", "BER": "베를린", "AMS": "암스테르담", 
    "MAD": "마드리드", "BCN": "바르셀로나", "FCO": "로마/피우미치노", "MXP": "밀라노/말펜사", 
    "VCE": "베네치아", "ZRH": "취리히", "GVA": "제네바", "VIE": "빈", 
    "CPH": "코펜하겐", "ARN": "스톡홀름", "OSL": "오슬로", "HEL": "헬싱키", 
    "LIS": "리스본", "ATH": "아테네", "IST": "이스탄불", "SAW": "이스탄불/사비하괵첸", 
    "DUB": "더블린", "BRU": "브뤼셀", "WAW": "바르샤바", "PRG": "프라하", 
    "BUD": "부다페스트", "SVO": "모스크바/셰레메티예보", "DME": "모스크바/도모데도보",

    # 중동/아프리카
    "DXB": "두바이", "AUH": "아부다비", "DOH": "도하", "JED": "제다", 
    "RUH": "리야드", "MCT": "무스카트", "BAH": "바레인", "KWI": "쿠웨이트", 
    "AMM": "암만", "TLV": "텔아비브", "CAI": "카이로", "CPT": "케이프타운", 
    "JNB": "요하네스버그", "NBO": "나이로비", "ADD": "아디스아바바",

    # 오세아니아
    "SYD": "시드니", "MEL": "멜버른", "BNE": "브리즈번", "PER": "퍼스", 
    "AKL": "오클랜드", "CHC": "크라이스트처치", "WLG": "웰링턴", "NAN": "나디"
}

# selectbox에 표시할 옵션 리스트 자동 생성
airport_options = []
for code, name in airport_data.items():
    cho = get_choseong(name)
    airport_options.append(f"{name} ({code}) - {cho}")

def extract_code(selected_option):
    return selected_option.split("(")[1].split(")")[0]

# --- 페이지 설정 ---
st.set_page_config(page_title="실시간 항공권 최저가 검색", layout="wide")
st.title("✈️ 실시간 항공권 최저가 검색기")

# --- 1. 사이드바: 검색 조건 및 필터링 ---
st.sidebar.header("검색 조건 설정")
st.sidebar.write("💡 영문 코드나 한글, 초성(예: ㅇㅊ, ㅈㅈ)으로 검색할 수 있습니다.")

default_origin = [opt for opt in airport_options if "ICN" in opt][0]
default_dest = [opt for opt in airport_options if "NRT" in opt][0]

selected_origin = st.sidebar.selectbox("출발지", options=airport_options, index=airport_options.index(default_origin))
selected_dest = st.sidebar.selectbox("도착지", options=airport_options, index=airport_options.index(default_dest))

origin_code = extract_code(selected_origin)
dest_code = extract_code(selected_dest)

# 경유 횟수에 "전체" 옵션 추가
stops_option = st.sidebar.radio("경유 횟수", ["전체", "직항", "1회 경유", "2회 이상 경유"])

st.sidebar.subheader("필터링")
max_price = st.sidebar.slider("최대 예산 (만원)", min_value=10, max_value=300, value=150, step=5)
max_layover = st.sidebar.slider("최대 경유 대기 시간 (시간)", min_value=0, max_value=24, value=12, step=1)

auto_refresh = st.sidebar.toggle("10초 자동 업데이트 켜기", value=False)

# --- 2. 가상 API 데이터 생성 함수 ---
def fetch_flight_data(origin, dest, stops, price_limit, layover_limit):
    airlines = ["대한항공", "아시아나", "제주항공", "진에어", "루프트한자", "에미레이트"]
    data = []
    
    stop_choices = ["직항", "1회 경유", "2회 이상 경유"]
    
    for _ in range(random.randint(5, 15)):
        price = random.randint(10, 300)
        
        # '전체'가 선택된 경우 직항/경유를 랜덤으로 배정
        if stops == "전체":
            actual_stops = random.choice(stop_choices)
        else:
            actual_stops = stops
            
        layover = random.randint(0, 24) if actual_stops != "직항" else 0
        
        if price <= price_limit and layover <= layover_limit:
            data.append({
                "항공사": random.choice(airlines),
                "출발지": origin,
                "도착지": dest,
                "경유 횟수": actual_stops,
                "경유 대기 시간(시간)": layover if actual_stops != "직항" else "-",
                "가격(만원)": price,
                # 한국 시간 기준으로 저장
                "업데이트 시간": datetime.now(KST).strftime("%H:%M:%S")
            })
            
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by="가격(만원)").reset_index(drop=True)
    return df

# --- 3. 메인 화면 구성 및 업데이트 로직 ---
data_placeholder = st.empty()
current_data = fetch_flight_data(origin_code, dest_code, stops_option, max_price, max_layover)

with data_placeholder.container():
    if current_data.empty:
        st.warning("조건에 맞는 항공권이 없습니다. 필터를 조정해 보세요.")
    else:
        current_time_str = datetime.now(KST).strftime('%H:%M:%S')
        st.success(f"최저가: {current_data['가격(만원)'].iloc[0]}만원 (한국 시간 기준: {current_time_str})")
        st.dataframe(current_data, use_container_width=True)

# 10초 자동 업데이트 로직
if auto_refresh:
    time.sleep(10)
    st.rerun()
