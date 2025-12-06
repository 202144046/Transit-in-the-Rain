import pandas as pd
import io

# -----------------------------------------------------------
# 1. 데이터 로드 (사용자가 제공한 예시 데이터 활용)
# -----------------------------------------------------------

# 지하철 데이터 (예시)
subway_csv = '../content/24년 서울교통공사_역별 일별 시간대별 승하차인원.csv'
# 날씨 데이터 (예시)
weather_csv = '../content/AWS시간별관측정보(2024년1월-2024년12월).csv'

df_subway = pd.read_csv(subway_csv)
df_weather = pd.read_csv(weather_csv)

# -----------------------------------------------------------
# 2. 지하철 데이터 전처리 (Melt: 가로 -> 세로 변환)
# -----------------------------------------------------------

# 시간대 컬럼만 리스트로 만들기 (06시 이전 ~ 24시 이후)
time_cols = [c for c in df_subway.columns if '06' in c or '~' in c or '24' in c]

# Melt 수행: 날짜, 역명 등을 고정하고 시간대별 승객수를 행으로 내림
df_subway_melted = df_subway.melt(
    id_vars=['날짜', '호선', '역번호', '역명', '구분'], 
    value_vars=time_cols,
    var_name='시간대_raw', 
    value_name='승객수'
)

# '06 ~ 07' 같은 문자열을 숫자(시간)로 변환하는 함수
def clean_subway_hour(text):
    if '06시 이전' in text: return 5  # 편의상 5시로 처리
    if '24시 이후' in text: return 24 # 편의상 24시로 처리
    return int(text.split('~')[0].strip()) # '06 ~ 07' -> 6

df_subway_melted['시간'] = df_subway_melted['시간대_raw'].apply(clean_subway_hour)
# 날짜 형식을 datetime으로 통일
df_subway_melted['날짜'] = pd.to_datetime(df_subway_melted['날짜'])

# -----------------------------------------------------------
# 3. 날씨 데이터 전처리 (대표 지점 선정 및 형식 통일)
# -----------------------------------------------------------

# (중요) 하나의 지역만 대표로 선정 (예: 파주시)
# 실제 데이터에서는 '광명시' 등 원하시는 지역명으로 변경하세요.
target_location = '파주시' 
df_weather_selected = df_weather[df_weather['시군명'] == target_location].copy()

# 날짜 변환 (20240101.0 -> datetime)
df_weather_selected['관측일자'] = df_weather_selected['관측일자'].astype(str).str.split('.').str[0]
df_weather_selected['날짜'] = pd.to_datetime(df_weather_selected['관측일자'], format='%Y%m%d')

# 시간 변환 (600.0 -> 6, 1200.0 -> 12)
# 데이터에 따라 0, 100, 200 방식일 수도 있고 0, 1, 2 방식일 수도 있습니다.
# 위 예시 데이터(600.0)를 기준으로 100을 나누어 시(Hour)를 추출합니다.
df_weather_selected['시간'] = (df_weather_selected['관측시간'] / 100).astype(int)

# 필요한 컬럼만 남기기 (키값 + 강수량)
weather_cols = ['날짜', '시간', '기온', '시간누적강우량']
df_weather_final = df_weather_selected[weather_cols]

# -----------------------------------------------------------
# 4. 데이터 병합 (Merge)
# -----------------------------------------------------------

# 지하철 데이터(Left)에 날씨 데이터(Right)를 '날짜'와 '시간' 기준으로 붙임
merged_df = pd.merge(df_subway_melted, df_weather_final, on=['날짜', '시간'], how='left')

# 강수량 결측치(NaN)는 0으로 채우거나(비가 안 옴), 혹은 측정 안됨으로 둘 수 있음
# 여기서는 비가 안 온 경우 데이터가 없을 수도 있으므로 0으로 채우는 예시
merged_df['시간누적강우량'] = merged_df['시간누적강우량'].fillna(0)

# 결과 확인
print("=== 병합된 데이터 미리보기 ===")
display(merged_df[['날짜', '역명', '시간', '승객수', '기온', '시간누적강우량']].head(10))

# -----------------------------------------------------------
# 5. 간단한 분석 예시 (비 오는 시간대의 역별 승객수)
# -----------------------------------------------------------
print("\n=== 강수량이 있는 시간대의 데이터 ===")
rainy_data = merged_df[merged_df['시간누적강우량'] > 0]
if not rainy_data.empty:
    display(rainy_data.head())
else:
    print("선택한 날짜/지역에 비가 온 데이터가 없습니다.")