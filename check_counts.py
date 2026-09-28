# check_counts.py
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:1234@localhost:3306/vehicle_db")

tables = ['car_registrations', 'ev_subsidies', 'ice_vehicles', 'faqs', 'charging_stations']

print("🔍 MySQL 테이블별 데이터 건수 확인:")
print("=" * 45)
with engine.connect() as conn:
    for t in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f" - {t:<20}: {count:>8,} 건")
        except Exception as e:
            print(f" - {t:<20}: 테이블 없음 또는 에러 ({e})")