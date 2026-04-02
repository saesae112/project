import streamlit as st
import base64

# 1. 로컬 이미지를 텍스트(Base64)로 변환하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        return ""

# 이미지 경로 설정
img_path = r"D:\project\images\DDAS_logo.png"
img_base64 = get_base64_image(img_path)

# 페이지 설정
st.set_page_config(layout="wide")
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">', unsafe_allow_html=True)

# 2. 헤더 구현 (f-string 적용 및 중복 제거)
st.markdown(
    f"""
    <style>
    .custom-header {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 70px;
        background-color: #000000; color: white;
        display: flex; justify-content: space-between; align-items: center;
        padding: 0 40px; z-index: 9999999;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .header-icons {{ display: flex; gap: 30px; }}
    .header-icons a {{ color: white; text-decoration: none; font-size: 20px; transition: 0.3s; }}
    .header-icons a:hover {{ color: #00aaff; transform: scale(1.2); }}
    
    .main .block-container {{ padding-top: 80px; }}
    section[data-testid="stSidebar"] {{ padding-top: 60px; }}
    header[data-testid="stHeader"] {{ display: none; }}
    </style>
    
    <div class="custom-header">
        <div class="header-logo">
            <img src="data:image/png;base64,{img_base64}" alt="DDAS Logo" style="height: 45px; width: auto;">
        </div>
        <div class="header-icons">
            <a href="/" target="_self" title="홈으로 이동"><i class="fa-solid fa-house"></i></a>
            <a href="/시나리오_분석" target="_self" title="이전 페이지"><i class="fa-solid fa-chevron-left"></i></a>
            <a href="-" target="_self" title="다음 페이지"><i class="fa-solid fa-circle-question"></i></a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("""
        <style>
            /* 1. DDAS(첫 번째 항목)를 메인 제목처럼 강조 */
            [data-testid="stSidebarNav"] ul li:nth-child(1) {
                background-color: transparent !important; /* 배경은 투명하게 */
                border-bottom: 2px solid #000000 !important; /* 하단에 진한 강조선 */
                margin-bottom: 15px !important; /* 하위 항목들과 간격 벌리기 */
                padding-bottom: 5px !important;
            }

            /* 2. DDAS 텍스트 스타일 */
            [data-testid="stSidebarNav"] ul li:nth-child(1) span {
                color: #000000 !important;
                font-weight: 800 !important; /* 아주 굵게 */
                font-size: 1.1rem !important; /* 글자 크기 약간 키움 */
            }

            /* 3. 하위 탭(나머지 항목들) 스타일 */
            [data-testid="stSidebarNav"] ul li:not(:first-child) {
                margin-left: 10px !important; /* 오른쪽으로 살짝 들여쓰기 */
                opacity: 0.8; /* 약간 흐리게 해서 하위 느낌 강조 */
            }
            
            /* 4. 하위 탭에 마우스 올렸을 때만 진하게 */
            [data-testid="stSidebarNav"] ul li:not(:first-child):hover {
                opacity: 1;
                background-color: #f0f2f6 !important;
            }

            /* 아이콘 색상 통일 */
            [data-testid="stSidebarNav"] ul li:nth-child(1) svg {
                fill: #007bff !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # ... 이후 가이드 코드
    with st.expander("**이용 가이드**", expanded=False):
        
        st.markdown("#### 데이터 탐색")
        st.caption("서울시 전역의 데이터를 지도에서 확인하고 분포를 파악합니다.")
        
        st.markdown("#### 후보자 조건 설정")
        st.caption("분석할 격자 영역을 생성하고, 방어무기 사정거리 및 시설별 가중치를 설정합니다.")
        
        st.markdown("#### 후보지 계산")
        st.caption("설정된 시나리오를 바탕으로 최적의 배치 지점을 알고리즘이 자동 산출합니다.")
        
        st.markdown("#### 결과 활용")
        st.caption("도출된 후보지의 상세 점수를 확인하고 여러 시나리오를 상호 비교합니다.")


    