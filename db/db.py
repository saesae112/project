from get_data.get import get_engine, disconnect_db, get_engine_server
from sqlalchemy import text

def upload_result(df):
 
    # DB 생성 
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS result CHARACTER SET utf8mb4"))
    disconnect_db(engine)

    # result DB에 연결
    engine = get_engine(db_name='result')

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'result' 
            AND table_name LIKE 'case%'
        """))
        tables = [str(row[0]) for row in result]
        if tables:
            max_index = max(int(t.replace('case', '')) for t in tables)
        else:
            max_index = 0

        next_index = max_index + 1

    table_name = f"case{next_index}"
    df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
    print(f"저장 완료: {table_name}")

    disconnect_db(engine)


def delete_result(case_name):
    engine = get_engine(db_name='result')
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{case_name}`"))  # 없는 테이블 삭제 시 오류 방지
        conn.commit()

    disconnect_db(engine)



######## SERVER ###########

def upload_result_server(df):
    # 1. DB 생성을 위해 'master'에 직접 연결 (캐시를 타지 않거나 명시적 인자 전달)
    # 캐시 때문에 꼬이는 걸 방지하기 위해 생성 로직에서는 
    # get_engine_server(db_name='master')를 확실히 호출한다.
    engine_master = get_engine_server(db_name='master')
    
    # isolation_level 설정 (이전 에러 해결책 적용)
    autocommit_engine = engine_master.execution_options(isolation_level="AUTOCOMMIT")
    
    with autocommit_engine.connect() as conn:
        # DB 존재 확인
        db_exists = conn.execute(text("SELECT COUNT(*) FROM sys.databases WHERE name = 'result'")).scalar()
        
        if not db_exists:
            print("🆕 'result' 데이터베이스가 없어 생성을 시도한다...")
            conn.execute(text("CREATE DATABASE result"))
            print("✅ 'result' 데이터베이스 생성 완료!")
        else:
            print("ℹ️ 'result' 데이터베이스가 이미 존재한다.")
            
    # 캐시된 엔진이라도 dispose()는 신중해야 함 (다른 곳에서 쓸 수 있음)
    # 하지만 생성 작업 직후에는 안전을 위해 명시적으로 세션을 정리하는 것이 좋음

    # 2. 데이터 적재를 위해 'result' DB에 연결
    engine_result = get_engine_server(db_name='result')
    
    try:
        with engine_result.connect() as conn:
            # 테이블 목록 확인 및 인덱스 계산
            res = conn.execute(text("SELECT name FROM sys.tables WHERE name LIKE 'case%'"))
            tables = [row[0] for row in res]
            
            indices = [int(t.replace('case', '')) for t in tables if t.replace('case', '').isdigit()]
            next_index = max(indices) + 1 if indices else 1
            table_name = f"case{next_index}"

            # 데이터 저장
            df.to_sql(name=table_name, con=engine_result, if_exists='replace', index=False)
            conn.commit()
            print(f"🚀 [{table_name}] 테이블에 저장 성공!")
    except Exception as e:
        print(f"❌ 데이터 적재 실패: {e}")


def delete_result_server(case_name):
    """
    result 데이터베이스에서 특정 결과 테이블(caseN)을 삭제한다.
    """
    # 1. result DB에 연결 (인자로 'result' 전달)
    engine = get_engine_server(db_name='result')
    
    try:
        with engine.connect() as conn:
            # 2. MSSQL 문법: 백틱(`) 대신 대괄호([]) 사용
            # DROP TABLE IF EXISTS는 MSSQL 2016 버전 이상부터 지원함
            print(f"🗑️ [{case_name}] 테이블 삭제 시도 중...")
            
            # 테이블 이름을 변수로 넣을 때는 대괄호로 감싸야 예약어/특수문자 충돌이 없다.
            query = text(f"DROP TABLE IF EXISTS [{case_name}]")
            conn.execute(query)
            
            # 3. SQLAlchemy 2.0 이상을 사용한다면 명시적 커밋 권장
            conn.commit()
            
            print(f"✅ [{case_name}] 삭제 완료!")
            
    except Exception as e:
        print(f"❌ 삭제 중 오류 발생: {e}")
        
    finally:
        # 4. 연결 해제 (dispose 또는 별도 함수 호출)
        engine.dispose()