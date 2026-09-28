import os
import glob
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "1234")
DB_NAME = os.getenv("DB_NAME", "vehicle_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(DATABASE_URL)

def parse_price_to_int(val) -> int:
    if pd.isna(val):
        return 0
    val_str = str(val).strip().replace(",", "").replace("원", "").replace("-", "")
    if not val_str:
        return 0
    try:
        return int(float(val_str))
    except ValueError:
        pass
    
    total = 0.0
    if "억" in val_str:
        parts = val_str.split("억")
        total += float(parts[0].strip() or 0) * 100000000
        val_str = parts[1] if len(parts) > 1 else ""
    if "만" in val_str:
        parts = val_str.split("만")
        total += float(parts[0].strip() or 0) * 10000
    return int(total)

def find_file(filename):
    if os.path.exists(filename):
        return filename
    # data/ 하위의 모든 세부 폴더(FAQ, 보조금, 전기차충전소 등)를 자동으로 찾음
    for root, dirs, files in os.walk("data"):
        if filename in files:
            return os.path.join(root, filename)
    return None

def read_csv_safe(path):
    fpath = find_file(path)
    if not fpath:
        return None
    for enc in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']:
        try:
            df = pd.read_csv(fpath, encoding=enc)
            df.columns = df.columns.str.strip()
            return df
        except Exception:
            continue
    return None

def init_db():
    with open("db/schema.sql", "r", encoding="utf-8") as f:
        cmds = f.read().split(";")
    with engine.begin() as conn:
        for cmd in cmds:
            if cmd.strip():
                conn.execute(text(cmd))
    print("✅ DB Schema Initialized.")

def load_registrations():
    path = os.path.join("data", "전국자동차등록현황", "전국자동차등록현황.csv")
    df = read_csv_safe(path)
    if df is None: return
    
    df = df.rename(columns={
        '연도': 'year', '월': 'month', '시도': 'sido', '시군구코드': 'sigungu_code',
        '지역': 'region', '등록대수': 'total_count', '내연기관': 'ice_count',
        '전기차': 'ev_count', '하이브리드': 'hybrid_count', '기타': 'etc_count'
    })
    
    for c in ['year', 'month', 'total_count', 'ice_count', 'ev_count', 'hybrid_count', 'etc_count']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    
    cols = ['year', 'month', 'sido', 'sigungu_code', 'region', 'total_count', 'ice_count', 'ev_count', 'hybrid_count', 'etc_count']
    with engine.begin() as conn:
        df[cols].to_sql('car_registrations', con=conn, if_exists='replace', index=False)
    print("✅ car_registrations loaded.")

def load_ev_subsidies():
    files = ["현대차_전기수소차_보조금_서울.csv", "현대차_전기수소차_보조금_경기도_전체.csv"]
    dfs = []
    for f in files:
        path = os.path.join("data", "보조금", f)
        d = read_csv_safe(path)
        if d is not None: 
            dfs.append(d)
            
    if not dfs: return
    full_df = pd.concat(dfs, ignore_index=True)
    
    # '넥쏘' 모델 제외
    full_df = full_df[~full_df['모델명'].str.contains('넥쏘', na=False)].copy()
    
    col_map = {
        '시/도': 'sido', '시/군/구': 'sigungu', 'url 주소': 'img_url',
        '모델명': 'model_name', '트림명': 'trim_name',
        '세제 혜택 후': 'price_after_tax', '세제 혜택 전': 'price_before_tax',
        '보조금': 'subsidy_total', '국가 보조금': 'subsidy_gov', '지자체 보조금': 'subsidy_local',
        '전환지원금': 'conversion_total', '국가 전환지원금': 'conversion_gov',
        '지자체 전환지원금': 'conversion_local', '최종가': 'final_price'
    }
    full_df = full_df.rename(columns=col_map)
    
    price_cols = ['price_after_tax', 'price_before_tax', 'subsidy_total', 'subsidy_gov', 
                  'subsidy_local', 'conversion_total', 'conversion_gov', 'conversion_local', 'final_price']
    
    for pc in price_cols:
        if pc in full_df.columns:
            full_df[pc] = full_df[pc].apply(parse_price_to_int)
            
    full_df['sido'] = full_df['sido'].replace({'경기도': '경기'})
    
    with engine.begin() as conn:
        full_df.to_sql('ev_subsidies', con=conn, if_exists='replace', index=False)
    print("✅ ev_subsidies loaded.")

def load_ice_vehicles():
    path = os.path.join("data", "보조금", "현대차_내연기관.csv")
    df = read_csv_safe(path)
    if df is None:
        df = read_csv_safe("현대_내연기관.csv")
    if df is None: return
    
    # trim 컬럼 및 transmission 컬럼을 DB 컬럼명(trim_name)으로 통일
    df = df.rename(columns={'trim': 'trim_name', 'transmission': 'trim_name'})
    df['price'] = df['price'].apply(parse_price_to_int)
    
    cols = ['category', 'model_name', 'trim_name', 'price', 'price_text', 'img_url']
    valid_cols = [c for c in cols if c in df.columns]
    
    with engine.begin() as conn:
        df[valid_cols].to_sql('ice_vehicles', con=conn, if_exists='replace', index=False)
    print("✅ ice_vehicles loaded.")

def load_charging_stations():
    station_files = [
        "서울_전기차충전소.csv", "경기도_전기차충전소.csv", "강원도_전기차충전소.csv",
        "충청도_전기차충전소.csv", "경상도_전기차충전소.csv", "전라도_전기차충전소.csv", "제주도_전기차충전소.csv"
    ]
    dfs = []
    for f in station_files:
        path = os.path.join("data", "전기차충전소", f)
        df = read_csv_safe(path)
        if df is not None and not df.empty:
            dfs.append(df)
                
    if not dfs:
        return

    full_df = pd.concat(dfs, ignore_index=True)
    
    col_map = {
        'statNm': 'stat_name', 'statId': 'stat_id', 'chgerId': 'chger_id',
        'chgerType': 'chger_type', 'addr': 'addr', 'lat': 'lat', 'lng': 'lng',
        'useTime': 'use_time', 'busiNm': 'busi_nm', 'output': 'output',
        'parkingFree': 'parking_free', 'region': 'region'
    }
    
    renamed_df = full_df.rename(columns=col_map)
    renamed_df['output'] = pd.to_numeric(renamed_df['output'], errors='coerce').fillna(0).astype(int)
    renamed_df['chger_id'] = pd.to_numeric(renamed_df['chger_id'], errors='coerce').fillna(0).astype(int)
    
    selected_cols = ['stat_name', 'stat_id', 'chger_id', 'chger_type', 'addr', 'lat', 'lng', 'use_time', 'busi_nm', 'output', 'parking_free', 'region']
    valid_df = renamed_df[[c for c in selected_cols if c in renamed_df.columns]]
    
    with engine.begin() as conn:
        valid_df.to_sql('charging_stations', con=conn, if_exists='replace', index=False, chunksize=10000)
    print("✅ 전국 charging_stations 적재 완료")

def load_faqs():
    faq_files = [
        ('FAQ_내연기관_기아.csv', '내연기관', '기아 (내연기관)'),
        ('FAQ_전기차_기아.csv', '전기차', '기아 (전기차)'),
        ('FAQ_전기차_epit.csv', '전기차', 'E-pit 충전'),
        ('FAQ_전기차_차지비.csv', '전기차', '차지비 충전'),
        ('FAQ_전기차_무공해차.csv', '전기차', '무공해차 보조금')
    ]
    
    dfs = []
    for fname, vtype, src in faq_files:
        path = os.path.join("data", "FAQ", fname)
        d = read_csv_safe(path)
        if d is not None:
            d = d.rename(columns={'question': '질문', 'answer': '답변'})
            d['vehicle_type'] = vtype
            d['source'] = src
            d = d.rename(columns={'질문': 'question', '답변': 'answer'})
            dfs.append(d[['vehicle_type', 'category', 'source', 'question', 'answer']])
    
    if dfs:
        full_faq = pd.concat(dfs, ignore_index=True)
        with engine.begin() as conn:
            full_faq.to_sql('faqs', con=conn, if_exists='replace', index=False)
        print("✅ faqs loaded.")

if __name__ == "__main__":
    init_db()
    load_registrations()
    load_ev_subsidies()
    load_ice_vehicles()
    load_faqs()
    print("🎉 ALL ETL PIPELINE TASKS COMPLETED!")