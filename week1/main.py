import pandas as pd
import numpy as np
import os, sys

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
  


if __name__ == '__main__':
  datapath = '../data/spending.csv'
  
  data = load_data(datapath)
  explore_structure(data)
  show_distribution(data)
  check_missing(data)
  numpy_amount_stats(data)
  