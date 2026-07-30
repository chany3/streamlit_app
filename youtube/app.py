import streamlit as st
import pandas as pd
import re
import plotly.express as px
from googleapiclient.discovery import build
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from konlpy.tag import Okt
from collections import Counter
import os

# 페이지 설정
st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📺", layout="wide")

st.title("📺 유튜브 댓글 분석기")
st.markdown("유튜브 영상의 댓글을 수집하여 **시간대별 작성 추이, 긍정/부정 반응도, 핵심 키워드(워드클라우드)**를 분석합니다.")

# --- 사이드바: 설정 영역 ---
st.sidebar.header("⚙️ 분석 설정")
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
video_url = st.sidebar.text_input("유튜브 영상 링크(URL)를 입력하세요")
max_comments = st.sidebar.slider("수집할 최대 댓글 수", min_value=50, max_value=1000, value=200, step=50)

# URL에서 Video ID 추출 함수
def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# 간단한 감성 분석 함수 (단어 사전 기반)
def analyze_sentiment(text):
    positive_words = ['좋', '최고', '감사', '응원', '재미', '기대', '완벽', '대박', '사랑', '멋', '화이팅']
    negative_words = ['별로', '최악', '노잼', '실망', '지루', '짜증', '아쉽', '논란', '문제']
    
    pos_score = sum(1 for word in positive_words if word in text)
    neg_score = sum(1 for word in negative_words if word in text)
    
    if pos_score > neg_score:
        return "긍정"
    elif neg_score > pos_score:
        return "부정"
    else:
        return "중립"

# --- 메인 로직 ---
if st.sidebar.button("분석 시작🚀"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    elif not video_url:
        st.error("유튜브 링크를 입력해주세요.")
    else:
        video_id = get_video_id(video_url)
        if not video_id:
            st.error("유효한 유튜브 링크가 아닙니다.")
        else:
            # 1. 영상 표시
            st.subheader("🎬 분석 대상 영상")
            st.video(video_url)
            
            # 2. 데이터 수집
            with st.spinner("댓글 데이터를 수집하고 분석하는 중입니다... (시간이 소요될 수 있습니다)"):
                try:
                    youtube = build('youtube', 'v3', developerKey=api_key)
                    comments = []
                    next_page_token = None
                    
                    while len(comments) < max_comments:
                        request = youtube.commentThreads().list(
                            part="snippet",
                            videoId=video_id,
                            maxResults=min(100, max_comments - len(comments)),
                            pageToken=next_page_token,
                            order="time"
                        )
                        response = request.execute()
                        
                        for item in response['items']:
                            snippet = item['snippet']['topLevelComment']['snippet']
                            comments.append({
                                '작성자': snippet['authorDisplayName'],
                                '작성일시': snippet['publishedAt'],
                                '댓글내용': snippet['textOriginal'],
                                '좋아요수': snippet['likeCount']
                            })
                            
                        next_page_token = response.get('nextPageToken')
                        if not next_page_token:
                            break
                            
                    df = pd.DataFrame(comments)
                    
                    if df.empty:
                        st.warning("수집된 댓글이 없습니다. 댓글이 사용 중지된 영상일 수 있습니다.")
                    else:
                        # 데이터 전처리
                        df['작성일시'] = pd.to_datetime(df['작성일시'])
                        df['날짜'] = df['작성일시'].dt.date
                        df['시간'] = df['작성일시'].dt.hour
                        df['반응도'] = df['댓글내용'].apply(analyze_sentiment)
                        
                        st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")
                        
                        # --- 탭 구성 ---
                        tab1, tab2, tab3, tab4 = st.tabs(["📈 시간대별 추이", "📊 댓글 반응도", "☁️ 워드클라우드", "📋 원본 데이터"])
                        
                        with tab1:
                            st.subheader("📈 시간대별 댓글 작성 추이")
                            trend_df = df.groupby(['날짜', '시간']).size().reset_index(name='댓글수')
                            trend_df['시간대'] = trend_df['날짜'].astype(str) + " " + trend_df['시간'].astype(str) + "시"
                            
                            fig_trend = px.line(trend_df, x='시간대', y='댓글수', markers=True, title='시간 흐름에 따른 댓글 수')
                            st.plotly_chart(fig_trend, use_container_width=True)
                            
                        with tab2:
                            st.subheader("📊 댓글 긍정/부정 반응도")
                            st.markdown("※ 간단한 긍정/부정 키워드 매칭을 통한 반응도 분석입니다.")
                            sentiment_counts = df['반응도'].value_counts().reset_index()
                            sentiment_counts.columns = ['반응도', '비율']
                            
                            fig_pie = px.pie(sentiment_counts, names='반응도', values='비율', 
                                             color='반응도', 
                                             color_discrete_map={'긍정':'#00CC96', '부정':'#EF553B', '중립':'#636EFA'})
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with tab3:
                            st.subheader("☁️ 한글 워드클라우드")
                            # 폰트 설정 (Streamlit Cloud 환경 고려)
                            font_path = "NanumGothic.ttf"
                            if not os.path.exists(font_path):
                                st.warning("⚠️ `NanumGothic.ttf` 폰트 파일이 없습니다. 기본 폰트를 사용하면 한글이 깨질 수 있습니다.")
                            
                            # 텍스트 추출 및 형태소 분석 (명사만 추출)
                            all_text = " ".join(df['댓글내용'].tolist())
                            okt = Okt()
                            nouns = okt.nouns(all_text)
                            
                            # 두 글자 이상 명사만 필터링
                            words = [n for n in nouns if len(n) > 1]
                            word_counts = Counter(words)
                            
                            if word_counts:
                                wc = WordCloud(
                                    font_path=font_path if os.path.exists(font_path) else None,
                                    background_color='white',
                                    width=800,
                                    height=400,
                                    colormap='viridis'
                                ).generate_from_frequencies(word_counts)
                                
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.imshow(wc, interpolation='bilinear')
                                ax.axis('off')
                                st.pyplot(fig)
                            else:
                                st.info("워드클라우드를 생성할 유의미한 한글 단어가 부족합니다.")
                                
                        with tab4:
                            st.subheader("📋 수집된 댓글 데이터")
                            st.dataframe(df[['작성일시', '작성자', '댓글내용', '좋아요수', '반응도']])
                            
                except Exception as e:
                    st.error(f"오류가 발생했습니다. API Key와 영상 URL을 다시 확인해 주세요.\n상세 오류: {e}")
