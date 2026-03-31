import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from glob import glob
import streamlit as st

def create_db_if_not_exists():
    db = st.secrets["mysql"]
    # 데이터베이스 이름을 제외한 기본 주소로 먼저 연결
    base_url = f"mysql+pymysql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/?charset={db['charset']}"
    # DB 생성 명령어를 즉시 반영하기 위해 AUTOCOMMIT 설정
    temp_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    
    try:
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db['database']} CHARACTER SET {db['charset']}"))
        print(f"✅ 0단계: [{db['database']}] 데이터베이스 확인 및 생성 완료")
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
    finally:
        temp_engine.dispose()

# 1. DB 연결
@st.cache_resource
def get_engine():
    db = st.secrets["mysql"]
    url = (
        f"mysql+pymysql://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['database']}"
        f"?charset={db['charset']}"
    )
    engine = create_engine(url, pool_pre_ping=True)
    return engine

# 2. DB 연결 테스트
def test_connection():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return result.scalar()

# 3. 데이터 넣기
def import_data():

    engine = get_engine()
    file_list = glob('final_data/*.csv')
    
    for file in file_list:
        df = pd.read_csv(file)
        
        # 1. 확장자(.csv) 제거 (예: df_area_density.csv -> df_area_density)
        raw_name = os.path.splitext(os.path.basename(file))[0]
        
        # 2. 맨 앞이 'df_'로 시작하면 해당 부분만 제거 (예: df_area_density -> area_density)
        file_name = raw_name[3:] if raw_name.startswith('df_') else raw_name
        
        df.to_sql(name=file_name, con=engine, if_exists='replace', index=False)
        print(f"[{file_name}] 테이블 적재 완료")

# 4. 데이터 가져오기 (Select)
def get_all_data(data_list):
    engine = get_engine()
    dfs = {}
    for data in data_list:
        query = f"""
            SELECT *
            FROM {data}
        """
        dfs[data] = pd.read_sql(query, engine)
        print(f"[{data}] 데이터 가져오기 완료")
    
    return dfs

# 5. 연결 해제 (Disconnect)
def disconnect_db(engine):
    engine.dispose()
    print("DB 연결 해제 완료")


# ---------------------------------------------------------
# 메인 실행 파이프라인 (Run)
# ---------------------------------------------------------
@st.cache_data
def get_dfs():
    print("=== 데이터베이스 파이프라인 시작 ===")
    
    create_db_if_not_exists()
    # 1단계: 연결
    engine = get_engine()
    
    # 2단계: 연결 상태 체크
    try:
        if test_connection() == 1:
            print("1/2단계: DB 연결 및 체크 성공")
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return None  # 연결 실패 시 파이프라인 중단
        
    # 3단계: 데이터 적재
    import_data()
    print("3단계: 모든 데이터 적재 완료")
    
    # 4단계: 적재된 데이터 다시 가져오기
    file_list = glob('final_data/*.csv')
    table_names = []
    
    for file in file_list:
        # 가져올 때도 똑같이 확장자를 떼고 'df_'를 제거하여 리스트 생성
        raw_name = os.path.splitext(os.path.basename(file))[0]
        table_name = raw_name[3:] if raw_name.startswith('df_') else raw_name
        table_names.append(table_name)
    
    dfs = get_all_data(table_names)
    print("4단계: 모든 데이터 가져오기 완료")
    
    # 5단계: 연결 해제
    disconnect_db(engine)
    print("5단계: 엔진 연결 해제 완료")
    
    print("=== 데이터베이스 파이프라인 실행 완료 ===")
    
    return dfs