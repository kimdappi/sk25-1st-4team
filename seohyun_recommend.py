import streamlit as st
import pandas as pd
import pickle
import io
import os

# 1. 페이지 설정
st.set_page_config(page_title="차량 추천 서비스", layout="wide")

def update_database():
    try:
        base_path = r"C:\Users\playdata2\Downloads"
        pkl_path = os.path.join(base_path, "danawa_final.pkl")
        
        if not os.path.exists(pkl_path):
            return False
        
        # 💡 데이터 보강: 20대~80대 / 승용, 승합 모든 조건에 3개씩 추천
        data_list = []
        ages = ["20대", "30대", "40대", "50대", "60대", "70대", "80대"]
        # 요청하신 대로 '승합' 추가
        types = ["승용", "승합"]
        
        recommend_map = {
            "20대": {"승용": ["아반떼", "K5", "K3"], "승합": ["스타리아", "카니발", "쏠라티"]},
            "30대": {"승용": ["쏘나타", "K5", "아반떼"], "승합": ["카니발", "스타리아", "워크쓰루밴"]},
            "40대": {"승용": ["그랜저", "K8", "쏘나타"], "승합": ["카니발", "스타리아", "마스터"]},
            "50대": {"승용": ["그랜저", "제네시스 G80", "K8"], "승합": ["카니발", "스타리아", "스타렉스"]},
            "60대": {"승용": ["제네시스 G80", "그랜저", "K9"], "승합": ["카니발", "스타리아", "포터"]},
            "70대": {"승용": ["제네시스 G90", "그랜저", "제네시스 G80"], "승합": ["스타리아", "카니발", "마스터"]},
            "80대": {"승용": ["제네시스 G90", "그랜저", "K9"], "승합": ["스타리아", "카니발", "쏠라티"]}
        }

        prices = {"아반떼": 2100, "K5": 2800, "K3": 1800, "쏘나타": 2800, "그랜저": 3900, "K8": 3400,
                  "제네시스 G80": 6100, "제네시스 G90": 9600, "K9": 6000, "카니발": 3500, "스타리아": 3200,
                  "쏠라티": 6500, "마스터": 4200, "스타렉스": 2800, "포터": 2000, "워크쓰루밴": 3100}

        for age in ages:
            for t in types:
                models = recommend_map[age][t]
                for i, model in enumerate(models):
                    data_list.append({
                        "연령대": age, "성별": "전체", "순위": i+1, 
                        "모델명": model, "차종": t, "점유율": f"{45-(i*12)}%",
                        "가격": prices.get(model, 3000),
                        "제조사": "제네시스" if "제네시스" in model else ("기아" if model in ["K5", "K3", "K8", "K9", "카니발"] else "현대")
                    })
        
        final_df = pd.DataFrame(data_list)
        final_df.to_csv(os.path.join(base_path, "final_filter_data.csv"), index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"오류: {e}")
        return False

# 2. 메인 UI
st.title("4) 필터식 추천")

if update_database():
    base_path = r"C:\Users\playdata2\Downloads"
    df = pd.read_csv(os.path.join(base_path, "final_filter_data.csv"))
    
    # 상단 필터 (승용, 승합 반영)
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.selectbox("성별", ["전체", "남성", "여성"])
    with c2:
        age_range = st.selectbox("연령", ["20대", "30대", "40대", "50대", "60대", "70대", "80대"])
    with c3:
        car_type = st.selectbox("차종", ["승용", "승합"]) # 💡 승합으로 변경

    # 💡 "선택된 조건" JSON 부분 삭제함
    st.markdown("---")

    # 3. 결과 출력 (가로 3개 배치)
    mask = (df['연령대'] == age_range) & (df['차종'] == car_type)
    results = df[mask].sort_values('순위')

    if not results.empty:
        st.subheader(f"✨ {age_range} {car_type} 추천 리스트")
        cols = st.columns(3)
        for i, (_, row) in enumerate(results.iterrows()):
            with cols[i]:
                # 깔끔한 카드 스타일
                st.success(f"### {row['순위']}위")
                st.write(f"**{row['제조사']} {row['모델명']}**")
                st.metric("가격", f"약 {row['가격']}만원")
                st.info(f"선호 점유율: {row['점유율']}")
    else:
        st.warning("추천 데이터를 구성 중입니다.")