import pandas as pd
import numpy as np

# 1. 데이터 로드
df_danawa = pd.read_pickle('danawa_final.pkl')

# 2. 선호도 데이터 맵
pref_map = {
    'gender': {
        '남성': ['쏘렌토', '팰리세이드', '스포티지', '그랜저', '카니발'],
        '여성': ['셀토스', '캐스퍼', '아반떼', '스포티지', '레이']
    },
    'age': {
        '20대': ['아반떼', '스포티지', '셀토스', 'K5', '투싼'],
        '30대': ['쏘렌토', '스포티지', '캐스퍼', '팰리세이드', '아반떼'],
        '40대': ['쏘렌토', '카니발', '팰리세이드', '레이', '캐스퍼'],
        '50대': ['그랜저', 'G80', '쏘렌토', '렉스턴 스포츠', '아반떼'],
        '60대': ['쏘나타', '그랜저', '렉스턴 스포츠', 'G80', '쏘렌토'],
    }
}

# 3. 승합/승용 분류
van_list = ['쏘렌토', '카니발', '스포티지', '팰리세이드', '싼타페', '셀토스', '투싼', '스타리아', 
            'GV70', 'GV80', '코나', 'EV3', '아이오닉 5', '니로', '베뉴', 'EV6', '아이오닉 9']

df_danawa['car_sort'] = df_danawa['model_name'].apply(lambda x: '승합' if any(m in x for m in van_list) else '승용')

def get_ultra_recommendation(gender, age, selected_type):
    df = df_danawa.copy()
    
    # 기본 시장 영향력 
    df['total_score'] = np.log1p(df['market_share'])
    
    # --- [보정 강도 설정] ---
    # 70대, 80대는 모든 인위적 보정(성별/연령)을 10% 수준으로 약화
    strength = 0.1 if age in ['70대', '80대'] else 1.0
    
    # 1. 성별 선호도 보정 (7080은 strength 적용으로 약화됨)
    if gender in pref_map['gender']:
        target_list = pref_map['gender'][gender]
        for i, model in enumerate(target_list):
            bonus = ((5 - i) * 20) * strength 
            df.loc[df['model_name'].str.contains(model), 'total_score'] += bonus
            
    # 2. 연령별 선호도 보정 (7080은 리스트가 없어 자동으로 0점 처리되나, strength 구조 유지)
    if age in pref_map['age']:
        target_list = pref_map['age'][age]
        for i, model in enumerate(target_list):
            bonus = ((5 - i) * 20) * strength
            df.loc[df['model_name'].str.contains(model), 'total_score'] += bonus

    # 필터링 및 결과 반환
    result = df[df['car_sort'] == selected_type].sort_values('total_score', ascending=False)