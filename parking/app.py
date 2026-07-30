import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import random
import os

# 페이지 설정
st.set_page_config(page_title="서울시 공영주차장 안내", page_icon="🚗", layout="wide")

# 데이터 불러오기 (캐싱하여 성능 최적화)
@st.cache_data
def load_data():
    # 현재 app.py 파일이 있는 폴더의 절대 경로를 가져옵니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 폴더 경로와 파일명을 합쳐서 정확한 위치를 지정해 줍니다.
    file_path = os.path.join(current_dir, "서울시 공영주차장 안내 정보.csv")
    
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8")
    
    # 위도, 경도 컬럼명 변경 및 결측치 제거
    df = df.dropna(subset=['위도', '경도'])
    df['lat'] = df['위도'].astype(float)
    df['lon'] = df['경도'].astype(float)
    
    # 주소에서 '자치구' 추출
    df['자치구'] = df['주소'].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else "알수없음")
    
    # 요금 관련 결측치를 0으로 채우기
    fee_cols = ['기본 주차 요금', '기본 주차 시간(분 단위)', '추가 단위 요금', '추가 단위 시간(분 단위)', '일 최대 요금']
    df[fee_cols] = df[fee_cols].fillna(0)
    
    return df

df = load_data()

st.title("🚗 서울시 공영주차장 정보 앱")
st.markdown("자치구별 공영주차장을 검색하고 지도와 그래프로 확인해 보세요. 예상 주차요금도 계산해 드립니다!")

# --- 사이드바: 검색 조건 설정 ---
st.sidebar.header("🔍 주차장 검색 조건")
gu_list = ["전체"] + sorted(df['자치구'].unique().tolist())
selected_gu = st.sidebar.selectbox("자치구를 선택하세요", gu_list)

type_list = ["전체"] + sorted(df['주차장 종류명'].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("주차장 종류를 선택하세요", type_list)

# 데이터 필터링
filtered_df = df.copy()
if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]
if selected_type != "전체":
    filtered_df = filtered_df[filtered_df['주차장 종류명'] == selected_type]

st.write(f"총 **{len(filtered_df)}**개의 주차장이 검색되었습니다.")

# --- 탭 구성 ---
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 지도 보기", "📊 통계 그래프", "💰 예상 요금 계산 & 추천", "🎲 랜덤 추천 & 다운로드"])

with tab1:
    st.subheader("📍 주차장 위치 지도")
    if not filtered_df.empty:
        # Pydeck을 이용한 지도 시각화
        layer = pdk.Layer(
            "ScatterplotLayer",
            filtered_df,
            get_position="[lon, lat]",
            get_radius=50,
            get_fill_color="[0, 150, 255, 160]",
            pickable=True,
        )
        # 검색된 지역의 중심점 찾기
        center_lat = filtered_df['lat'].mean()
        center_lon = filtered_df['lon'].mean()
        
        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12, pitch=0)
        st.pydeck_chart(pdk.Deck(
            layers=[layer], 
            initial_view_state=view_state,
            tooltip={"text": "{주차장명}\n주소: {주소}\n총 주차면: {총 주차면}면"}
        ))
    else:
        st.warning("조건에 맞는 주차장이 없습니다.")

with tab2:
    st.subheader("📊 주차면 수 Top 10 주차장")
    if not filtered_df.empty:
        top10_df = filtered_df.nlargest(10, '총 주차면')
        fig = px.bar(top10_df, x='주차장명', y='총 주차면', color='총 주차면', 
                     text='총 주차면', title="가장 주차면이 많은 주차장 Top 10")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("데이터가 없습니다.")

with tab3:
    st.subheader("💰 예상 주차 요금 계산기")
    st.markdown("선택한 지역(조건) 내의 주차장 중 예상 요금이 가장 저렴한 곳을 추천해 드립니다.")
    
    hours = st.number_input("예상 주차 시간(시간 단위로 입력, 예: 2.5 = 2시간 30분)", min_value=0.5, value=2.0, step=0.5)
    total_minutes = int(hours * 60)
    
    if st.button("요금 계산 및 최저가 추천"):
        if not filtered_df.empty:
            def calculate_fee(row):
                base_fee = row['기본 주차 요금']
                base_time = row['기본 주차 시간(분 단위)']
                add_fee = row['추가 단위 요금']
                add_time = row['추가 단위 시간(분 단위)']
                daily_max = row['일 최대 요금']
                
                # 기본 정보가 없으면 계산 불가 처리 (무한대)
                if base_time == 0 or add_time == 0:
                    return float('inf')
                
                if total_minutes <= base_time:
                    fee = base_fee
                else:
                    extra_time = total_minutes - base_time
                    import math
                    extra_units = math.ceil(extra_time / add_time)
                    fee = base_fee + (extra_units * add_fee)
                
                # 일 최대 요금이 설정되어 있고, 계산된 요금이 일 최대 요금보다 크면 일 최대 요금 적용
                if daily_max > 0 and fee > daily_max:
                    fee = daily_max
                    
                return fee

            calc_df = filtered_df.copy()
            calc_df['예상요금(원)'] = calc_df.apply(calculate_fee, axis=1)
            
            # 계산 불가(inf)인 데이터 제외
            valid_df = calc_df[calc_df['예상요금(원)'] != float('inf')]
            
            if not valid_df.empty:
                # 예상 요금 기준 오름차순 정렬
                valid_df = valid_df.sort_values(by='예상요금(원)')
                cheapest = valid_df.iloc[0]
                
                st.success(f"🏆 **가장 저렴한 주차장 추천:** {cheapest['주차장명']}")
                st.write(f"- **주소:** {cheapest['주소']}")
                st.write(f"- **예상 요금:** {int(cheapest['예상요금(원)'])}원 (이용 시간: {hours}시간)")
                st.write(f"- **기본 요금:** {int(cheapest['기본 주차 요금'])}원 / {int(cheapest['기본 주차 시간(분 단위)'])}분")
                
                st.markdown("---")
                st.write("📋 **선택 조건 내 주차장 예상 요금 리스트 (저렴한 순)**")
                display_cols = ['주차장명', '주소', '총 주차면', '예상요금(원)']
                st.dataframe(valid_df[display_cols].head(10).reset_index(drop=True))
            else:
                st.error("요금 정보가 충분하지 않아 계산할 수 없습니다.")
        else:
            st.warning("검색된 주차장이 없습니다.")

with tab4:
    st.subheader("🎲 주차장 랜덤 추천")
    if st.button("랜덤으로 주차장 하나 뽑기"):
        if not filtered_df.empty:
            random_choice = filtered_df.sample(1).iloc[0]
            st.info(f"✨ **오늘의 추천 주차장:** {random_choice['주차장명']}")
            st.write(f"- **주소:** {random_choice['주소']}")
            st.write(f"- **총 주차면:** {random_choice['총 주차면']}면")
            st.write(f"- **전화번호:** {random_choice['전화번호'] if pd.notna(random_choice['전화번호']) else '정보 없음'}")
        else:
            st.warning("검색된 주차장이 없습니다.")
            
    st.markdown("---")
    st.subheader("💾 검색 결과 다운로드")
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="CSV 파일 다운로드",
            data=csv,
            file_name='seoul_parking_lots.csv',
            mime='text/csv',
        )
