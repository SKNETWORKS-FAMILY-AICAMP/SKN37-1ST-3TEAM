CREATE DATABASE IF NOT EXISTS vehicle_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vehicle_db;

-- 1. 자동차 등록 현황 통계 테이블
CREATE TABLE IF NOT EXISTS car_registrations (
    reg_id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL COMMENT '연도',
    month INT NOT NULL COMMENT '월',
    sido VARCHAR(50) NOT NULL COMMENT '시/도',
    sigungu_code INT COMMENT '시군구코드',
    region VARCHAR(50) NOT NULL COMMENT '지역명',
    total_count INT DEFAULT 0 COMMENT '총 등록대수',
    ice_count INT DEFAULT 0 COMMENT '내연기관 대수',
    ev_count INT DEFAULT 0 COMMENT '전기차 대수',
    hybrid_count INT DEFAULT 0 COMMENT '하이브리드 대수',
    etc_count INT DEFAULT 0 COMMENT '기타 차량 대수',
    INDEX idx_year_month_sido (year, month, sido)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 전기/수소차 지자체 보조금 및 최종가 테이블 (서울, 경기)
CREATE TABLE IF NOT EXISTS ev_subsidies (
    ev_id INT AUTO_INCREMENT PRIMARY KEY,
    sido VARCHAR(50) NOT NULL COMMENT '시/도',
    sigungu VARCHAR(50) NOT NULL COMMENT '시/군/구',
    img_url VARCHAR(500) COMMENT '차량 이미지 URL',
    model_name VARCHAR(100) NOT NULL COMMENT '모델명',
    trim_name VARCHAR(100) NOT NULL COMMENT '트림명',
    price_after_tax INT DEFAULT 0 COMMENT '세제 혜택 후 (원)',
    price_before_tax INT DEFAULT 0 COMMENT '세제 혜택 전 (원)',
    subsidy_total INT DEFAULT 0 COMMENT '총 보조금 (원)',
    subsidy_gov INT DEFAULT 0 COMMENT '국가 보조금 (원)',
    subsidy_local INT DEFAULT 0 COMMENT '지자체 보조금 (원)',
    conversion_total INT DEFAULT 0 COMMENT '전환지원금 (원)',
    conversion_gov INT DEFAULT 0 COMMENT '국가 전환지원금 (원)',
    conversion_local INT DEFAULT 0 COMMENT '지자체 전환지원금 (원)',
    final_price INT NOT NULL COMMENT '최종 실구매가 (원)',
    INDEX idx_sido_sigungu (sido, sigungu),
    INDEX idx_final_price (final_price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 내연기관 차량 스펙 및 가격 테이블
CREATE TABLE IF NOT EXISTS ice_vehicles (
    ice_id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50) COMMENT '차종 카테고리',
    model_name VARCHAR(100) NOT NULL COMMENT '모델명',
    trim_name VARCHAR(100) COMMENT '변속기/트림명',
    price INT NOT NULL COMMENT '가격 (원)',
    price_text VARCHAR(50) COMMENT '표시용 가격 문구',
    img_url VARCHAR(500) COMMENT '이미지 URL',
    INDEX idx_model_name (model_name),
    INDEX idx_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 4. 전국 전기차 충전소 인프라 테이블
CREATE TABLE IF NOT EXISTS charging_stations (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    stat_name VARCHAR(150) NOT NULL COMMENT '충전소명',
    stat_id VARCHAR(50) NOT NULL COMMENT '충전소ID',
    chger_id INT COMMENT '충전기ID',
    chger_type VARCHAR(20) COMMENT '충전기타입',
    addr VARCHAR(255) COMMENT '소재지 도로명주소',
    lat DECIMAL(10, 8) COMMENT '위도',
    lng DECIMAL(11, 8) COMMENT '경도',
    use_time VARCHAR(100) COMMENT '이용가능시간',
    busi_nm VARCHAR(100) COMMENT '운영기관명',
    output INT DEFAULT 0 COMMENT '충전용량(kW)',
    parking_free CHAR(1) DEFAULT 'N' COMMENT '주차료무료여부(Y/N)',
    region VARCHAR(50) NOT NULL COMMENT '권역 (서울, 경기 등)',
    INDEX idx_region_stat (region, stat_name),
    INDEX idx_lat_lng (lat, lng)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 자동차 및 전기차 통합 FAQ 테이블
CREATE TABLE IF NOT EXISTS faqs (
    faq_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_type VARCHAR(20) NOT NULL COMMENT '차량 구분 (전기차, 내연기관 등)',
    category VARCHAR(50) NOT NULL COMMENT '세부 카테고리 (보조금, 충전, 정비 등)',
    source VARCHAR(100) COMMENT '정보 출처',
    question TEXT NOT NULL COMMENT '질문',
    answer TEXT NOT NULL COMMENT '답변',
    INDEX idx_type_category (vehicle_type, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;