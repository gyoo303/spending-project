import os, sys
import sqlite3
import sqlalchemy
import pandas as pd

DATA_PATH = '../data/spending_clean.csv'
DB_PATH = '../data/spendings.db'

def load_clean_data(path):
  """pandas의 read_csv()로 CSV 파일을 불러와 DataFrame으로 반환합니다."""
  # 파일 경로를 인자로 받아 DataFrame을 반환합니다
  # 파일이 존재하지 않을 경우 안내 메시지를 출력하고 프로그램을 종료합니다
  # 불러오기 성공 시 "데이터 로드 완료: 행 수 × 열 수" 형태로 출력합니다

  if os.path.exists(path):
    df = pd.read_csv(path, encoding='utf-8-sig')
    print(f"데이터 로드 완료: {df.shape[0]}행 x {df.shape[1]}열")
    return df
  else:
    sys.exit(1)


# 기능 1 — DB 연결 + 테이블 생성 (init_db)
def init_db(path):
  """SQLite 데이터베이스에 연결하고, 지출 데이터를 담을 테이블을 만듭니다."""
  # data/ 폴더가 없으면 만들고, sqlite3.connect로 DB에 연결합니다 (파일이 없으면 자동 생성)
  # 아래 스키마로 spendings 테이블을 만듭니다 (재실행을 위해 기존 테이블은 지우고 새로 생성)
  # 테이블·기본키·NOT NULL의 의미를 주석으로 남깁니다
  
  if not os.path.exists("../data"):
    os.makedirs("../data")

  conn = sqlite3.connect(path)
  cursor = conn.cursor()  
  cursor.execute(
    """
    DROP TABLE IF EXISTS spendings
    """,
  )
  conn.commit()
  
  cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS spendings (
        record_id TEXT PRIMARY KEY NOT NULL,
        date DATE,
        category TEXT,
        item TEXT,
        amount INTEGER,
        payment TEXT,
        memo TEXT,
        year INTEGER,
        month INTEGER,
        day INTEGER,
        amount_level TEXT
        )
    """,
    )
  conn.commit()

  return conn


# 기능 2 — 정제 데이터 저장 (save_to_db)
def save_to_db(df, conn):
  """과제 2 정제본을 불러와 spendings 테이블에 저장합니다."""
  # pandas의 to_sql로 DataFrame을 테이블에 저장합니다
  # 기능 1에서 만든 스키마(기본키·NOT NULL)를 유지하기 위해 if_exists="append"를 사용합니다
  # 저장 후 COUNT(*)로 실제 저장된 행 수를 확인해 출력합니다
  
  df.to_sql("spendings", conn, if_exists="append", index=False)
  
  cursor = conn.cursor()
  cursor.execute("SELECT COUNT(*) FROM spendings")
  count = cursor.fetchone()[0]
  print(f"기능2 : 저장된 행 수: {count}")
    
  return None


# 기능 3 — 기본 조회 (SELECT)
def query_basic(conn, column = None):
  """pd.read_sql로 테이블 데이터를 조회합니다."""
  # 전체에서 상위 5행을 조회합니다
  # 필요한 컬럼만 골라 조회합니다
  
  print("기능3 기본 조회:")
  if column:
    print(pd.read_sql(f"SELECT {column} FROM spendings LIMIT 5", conn))
  else:
    print(pd.read_sql("SELECT * FROM spendings LIMIT 5", conn))
  
  return None

# 기능 4 — 조건 조회 (WHERE + ORDER BY)
def query_conditional(conn, condition = ""):
  """WHERE로 조건을 걸고 ORDER BY로 정렬해 원하는 데이터만 조회합니다."""
  # 특정 카테고리(예: 식비)를 금액 높은 순으로 조회합니다
  # 여러 조건을 AND로 결합해 조회합니다 (예: 3만 원 이상 & 카드 결제)
  
  print(f"기능4 조건 조회 - {condition}:")
  print(pd.read_sql(f"SELECT * FROM spendings {condition} ORDER BY amount DESC", conn))
  
  return None
  
# 기능 5 — 집계 조회 (GROUP BY)
def query_groupby(conn):
  "GROUP BY로 카테고리별·월별 지출을 집계합니다."
  # 카테고리별 건수·총지출·평균·최대 금액을 조회합니다 (총지출 내림차순)
  # 월별 건수·총지출을 조회합니다
  
  sql_groupby_result = [pd.read_sql(f"""
    SELECT 
      {groupby_target},
      COUNT(*) AS tot_count,
      SUM(amount) AS tot_amount,
      AVG(amount) AS avg_amount, 
      MAX(amount) AS max_amount 
    FROM spendings
    GROUP BY {groupby_target}
    ORDER BY tot_amount DESC
    """, conn)
    for groupby_target in ['category', 'month']
  ]
  
  print(f"기능5 집계 조회: {sql_groupby_result}")
  
  return sql_groupby_result
  
# 기능 6 — Python vs SQL 검증 + main() 연결
def verify_sql_to_df(df, conn):
  """Python으로 계산한 집계와 SQL 집계가 같은지 확인하고, 전체를 main()에서 연결합니다."""
  # Python(groupby)으로 카테고리별 총지출을 계산합니다
  # SQL(GROUP BY)로 같은 값을 조회합니다
  # 두 결과를 합쳐 일치 여부를 출력합니다
  
  is_verified = False
  
  tot_amount_groupby_cat_pandas = df.groupby('category')[['amount']].sum()\
    .sort_values(by='amount', ascending=False)\
    .reset_index()\
    .rename(columns = {'amount' : 'tot_amount'})
    
  tot_amount_groupby_cat_sql = query_groupby(conn)[0][['category', 'tot_amount']]
  
  # print(tot_amount_groupby_cat_pandas)
  # print(tot_amount_groupby_cat_sql)
  
  is_verified = tot_amount_groupby_cat_pandas.eq(
                  tot_amount_groupby_cat_sql
                ).all(axis=None)

  print(f"전체 카테고리 일치 : {is_verified}")
  
  return None



if __name__ == '__main__':
  # main()에서 로드 → DB 생성 → 저장 → 조회 → 검증을 순서대로 호출합니다
  
  df = load_clean_data(DATA_PATH)
  conn = init_db(DB_PATH)
  
  save_to_db(df, conn)
  
  query_basic(conn)
  query_basic(conn, column = 'category, payment')  
  query_conditional(conn, condition="WHERE amount >= 30000 AND payment = '카드'")  
  query_groupby(conn)
  
  verify_sql_to_df(df, conn)

  conn.close()