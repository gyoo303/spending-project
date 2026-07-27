import pandas as pd
import numpy as np
import os, sys

DATA_PATH = '../data/spending.csv'

# 기능 1 - 데이터 불러오기
def load_data(path):
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

# 기능 2 - 데이터 구조 확인
def explore_structure(df):
  """불러온 DataFrame의 기본 구조를 파악합니다."""
  # 전체 행 수와 열 수를 출력합니다
  # 각 컬럼의 이름과 자료형을 출력합니다
  # 상위 5행을 출력해 실제 데이터 형태를 확인합니다
  # 각 출력 블록마다 구분선(=====)과 제목을 붙여 가독성 있게 표시합니다

  print(df.shape)
  print("=====")
  print({c:d for c,d in zip(list(df.columns), list(df.dtypes))})
  print("=====")
  print(df.head())
  
  return None
  
# 기능 3 - 분포 확인
def show_distribution(df):
  """지출 데이터가 카테고리별·결제 수단별로 어떻게 분포되어 있는지, 카테고리별 평균 금액은 얼마인지 파악합니다."""  
  # 카테고리별 지출 건수와 전체 대비 비율(%)을 출력합니다
  # 결제 수단(카드/현금)별 건수와 비율(%)을 출력합니다
  # 반복문과 딕셔너리를 사용해 카테고리별 평균 금액을 계산하고 출력합니다
  # 결과를 딕셔너리로 반환합니다
  
  def print_count_and_percent_info(pd_series):
    print(pd.concat([pd_series.value_counts(),
                      pd.DataFrame(pd_series.value_counts()).rename(columns={'count':'percent'}) / pd_series.value_counts().sum()],
                      axis=1))
    
  print_count_and_percent_info(df['category']) 
  print_count_and_percent_info(df['payment'])
  
  result = {catname:pd.Series.mean(df[df['category']==catname]['amount'])
            for catname in df['category'].unique()}
  print(result)  
  return result


# 기능 4 - 결측치 현황 파악
def check_missing(df):
  """각 컬럼에 결측치가 몇 개, 몇 %나 있는지 파악하고 심각도를 판단합니다."""
  # 컬럼별 결측치 수와 비율(%)을 계산합니다
  # 결측치가 1개 이상인 컬럼만 출력합니다
  # 결측치 비율을 기준으로 심각도를 구분해 출력합니다 (낮음 <5% / 주의 5%~20% / 높음 >=20%)
  # 결측치가 없는 컬럼 목록도 함께 출력합니다
  # 결과를 딕셔너리로 반환합니다
  
  def check_null_degree(percent):
    if percent < .05:
      return "낮음"
    elif percent > .2:
      return "주의"
    else:
      return "높음"
  
  null_count_by_col = pd.concat([df.isnull().sum(), df.isnull().mean()], axis=1)
  null_count_by_col.columns = ['null_count', 'null_percent']

  print(null_count_by_col)  
  print(df.loc[:, df.isnull().sum() > 0])

  col_names_by_null_degree = null_count_by_col['null_percent'].apply(check_null_degree).to_dict()
  print(col_names_by_null_degree)
    
  return col_names_by_null_degree

# 기능 5 — NumPy로 금액 통계량 계산 
def numpy_amount_stats(df):
  # amount 컬럼 값으로 NumPy 배열을 만듭니다
  # 결측치가 있는 행은 배열 생성 전에 제거합니다
  # 아래 5가지 통계량을 NumPy 함수로 각각 계산합니다: 평균, 표준편차, 중앙값, 최솟값, 최댓값
  # 조건 필터링으로 "5만 원 초과 지출" 건을 찾아 출력합니다
  # pandas describe()로 계산한 결과와 수치를 비교해 일치하는지 확인하는 출력을 포함합니다
    
  arr_amount = np.array(df.dropna()['amount'])  
  np_stats = pd.Series(
              [np.mean(arr_amount),
              np.std(arr_amount, ddof=1),
              np.median(arr_amount),
              np.min(arr_amount),
              np.max(arr_amount)],
              index = ['mean', 'std', '50%', 'min', 'max']
  )  
  pd_stats = df.dropna()['amount'].describe().loc[['mean', 'std', '50%', 'min', 'max']]
  
  print(arr_amount[arr_amount > 50000.0])
  print(pd.concat([np_stats, pd_stats, np_stats == pd_stats],
                  axis=1).rename(columns={0:'np_stats', 'amount':'pd_stats', 1:'is_same'}))
    
  return None
  
  
# Week2 기능 1 — 날짜 파싱 및 파생 컬럼 생성 (parse_dates)
def parse_dates(df):
  """문자열로 된 날짜를 datetime 타입으로 바꾸고, 연·월·일 컬럼을 추가합니다. 날짜가 datetime이어야 월별 집계나 정렬을 정확히 할 수 있습니다."""
  # date 컬럼을 pd.to_datetime으로 변환합니다 (errors="coerce"로 변환 실패는 NaT 처리)
  # 변환에 실패한 행이 몇 개인지 출력합니다
  # year, month, day 파생 컬럼을 만듭니다

  df_new = df.copy()
  df_new['date'] = pd.to_datetime(df_new['date'], format="%Y-%m-%d", errors="coerce")
  
  print(df_new['date'].isna().sum())
  
  df_new['year'] = df_new['date'].dt.year
  df_new['month'] = df_new['date'].dt.month
  df_new['day'] = df_new['date'].dt.day
  
  print(df_new.head())
  
  return df_new

# Week2 기능 2 — 카테고리 표준화 (standardize_category)
def standardize_category(df):
  """CSV를 직접 입력하다 보면 오탈자·공백 같은 표기 불일치가 생길 수 있습니다. 함수로 이를 정리합니다."""
  # 앞뒤 공백을 제거합니다
  # 허용 목록(식비/교통/쇼핑/의료/문화/기타)에 있으면 그대로 두고, 없으면 기타로 바꿉니다
  # 문자열이 아니면 기타로 처리합니다
  
  def standardize(text):
    standard_values = ['식비', '교통', '쇼핑', '의료', '문화', '기타']
    
    if isinstance(text, str):
      text = text.strip()
      if text not in standard_values:
        text = '기타'
    
    else:
      text = '기타'
    
    return text
  
  df_new = df.copy()
  df_new['category'] = df_new['category'].apply(standardize)
  
  print(df_new['category'].value_counts())
    
  return df_new


# Week2 기능 3 — 금액 구간 컬럼 생성 (add_amount_level)
def add_amount_level(df):
  """조건문으로 금액을 세 구간으로 나눈 amount_level 컬럼을 추가합니다."""
  # 구간 기준:
  # 소액 1만 원 미만
  # 중액 1만 원 이상 ~ 5만 원 미만
  # 고액 5만 원 이상
  
  def check_amount(num):
    if num < 10000.0:
      return '소액'
    elif num < 50000.0:
      return '중액'
    else:
      return '고액'
  
  df_new = df.copy()
  df_new['amount_level'] = df_new['amount'].apply(check_amount) 
  
  return df_new


# Week2 기능 4 — 결측·이상값 처리 (clean_values)
def clean_values(df):
  """메모 결측치를 채우고, 금액이 0 이하이거나 날짜 변환에 실패한 행을 제거합니다."""
  # memo 결측치를 빈 문자열("")로 채웁니다
  # 금액이 0 이하인 행을 제거합니다
  # 날짜 변환에 실패한(NaT) 행을 제거합니다
  # 제거 전/후 행 수를 출력합니다
  
  df_new = df.copy()
  
  df_new = df_new.fillna({"memo" : ""})
  df_new = df_new[df_new["amount"] > 0.0]
  df_new = df_new.dropna(subset=["date"])
  df_new = df_new.reset_index(drop=True)
  
  print(df['memo'].isna().sum(), df_new['memo'].isna().sum())
  print(len(df), len(df_new))
  
  return df_new


# Week2 기능 5 — 간단 집계로 확인 (show_summary)
def show_summary(df):
  """정리된 데이터가 말이 되는지 월별·카테고리별 합계로 확인합니다. groupby로 간단히 계산합니다."""
  # 월별 총 지출을 계산해 출력합니다
  # 카테고리별 총 지출을 (많은 순으로) 출력합니다
  
  print(df.groupby("month")["amount"].sum())
  print(df.groupby("category")["amount"].sum().sort_values(ascending=False))
    
  return None


if __name__ == '__main__':
  print(pd.__version__)   # 예: 2.1.0
  print(np.__version__)   # 예: 1.26.0
  
  data = load_data(DATA_PATH)

  # week1
  # explore_structure(data)
  # show_distribution(data)
  # check_missing(data)
  # numpy_amount_stats(data)
  
  # week2
  data = parse_dates(data)
  data = standardize_category(data)
  data = add_amount_level(data)
  data = clean_values(data)
  show_summary(data)
  
  data.to_csv('../data/spending_clean.csv', index=False, encoding='utf-8-sig')
  