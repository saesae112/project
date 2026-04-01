import streamlit as st
import pandas as pd
import pymysql

# DESIGN implement changes to the standard streamlit UI/UX
st.set_page_config(page_title="D-DAS", page_icon="images/technology.png", layout="wide", initial_sidebar_state="collapsed")
    
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def get_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        charset="utf8mb4"
    )

# 회원가입 스타일
st.markdown("""
<style>
[data-testid="stPageLink"] a {
    color: #4c8bf5 !important;
    text-decoration: underline !important;
    font-size: 14px !important;
    transition: color 0.2s ease, letter-spacing 0.15s ease !important;
    display: inline-block !important;
}
[data-testid="stPageLink"] a:hover {
    color: #1a3fa3 !important;
    letter-spacing: 0.5px !important;
}
</style>
""", unsafe_allow_html=True)

# 제 맘대로 drone defense allocaton system -> D - DAS로 지어봤습니다 ㅎㅎ
with st.container():
    col1, col2= st.columns([5, 1])
    with col1:
        st.title('D-DAS :')
        st.subheader( 'Drone Defense Allocation System')
    with col2:
        st.image('images/technology.png', width=200)

st.divider()

chan1, id_log=st.columns([5,2])

with chan1:
    st.write('')

with id_log:
    with st.container(border=True,width=500,horizontal_alignment='center'):
        st.write('')
        st.write('')
        input_sender = st.text_input('', placeholder='id')

        input_recipient = st.text_input('',placeholder='password',type='password')
        st.write('')
        st.write('')
        st.write('')
        st.write('')

        sub_butt=st.button('Submit')
    st.caption("계정이 없으신가요?",text_alignment='right')
    col1,col2=st.columns([4,1])
    with col2:  
        st.page_link("pages/회원가입.py", label="회원가입")
        



if sub_butt:
    conn=get_connection()
    with conn.cursor() as cursor:
        sql = "SELECT * FROM users WHERE user_id = %s AND password = %s"
        cursor.execute(sql, (input_sender, input_recipient))
        
        if cursor.fetchone():
            st.session_state.logged_in = True
            st.switch_page("pages/1_입지 분석.py")
            
        

    # 이거는 이후에 로컬 환경에서 작동시킬 때는 my sql이랑 연동해서 
    # 로그인 가능한지 확인해서 page 넘어갈 수 있도록 할 것입니다. 


col_a, col_b, col_c = st.columns([1, 1, 1])

