# check_db.py
# DB 조회 오류확인

import pandas as pd
from sqlalchemy import create_engine, text

# 본인 DB 접속 정보로 확인
engine = create_engine("mysql+pymysql://root:1234@localhost:3306/vehicle_db")

try:
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM car_registrations LIMIT 1;"), conn)
        print("📌 현재 car_registrations 테이블의 컬럼 목록:")
        print(list(df.columns))
except Exception as e:
    print("❌ DB 조회 오류:", e)