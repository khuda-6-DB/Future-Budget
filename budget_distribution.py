import pandas as pd

def calc_original_ratios(df):
    original_ratios = {
    '식비': 0,
    '카페, 간식': 0,
    '편의점, 마트': 0,
    '술, 유흥': 0,
    '생활, 쇼핑': 0,
    '패션, 뷰티': 0,
    '취미, 여가, 운동': 0,
    '의료': 0,
    '주거, 통신': 0,
    '교통, 자동차': 0,
    '여행, 숙박': 0,
    '교육': 0,
    '이체': 0,
    '간편 결제': 0,
    '기타': 0
    }
    category_month_sum = df.groupby(['월', '카테고리'])['출금액'].sum().unstack(fill_value=0)
    category_total_sum = category_month_sum.sum()
    category_ratios = (category_total_sum / category_total_sum.sum()) * 100
    for key in original_ratios:
        original_ratios[key] = category_ratios.to_dict().get(key, 0)

    exclude_categories = ["간편 결제", "이체", "기타"]
    filtered_ratios = {k: v for k, v in original_ratios.items() if k not in exclude_categories}
    categories = list(filtered_ratios.keys())
    weights = [1.0] * len(categories)  # 각 카테고리의 초기 가중치를 1로 설정
    df = pd.DataFrame({'카테고리': categories, '원래 비율': list(filtered_ratios.values()), '가중치': weights})

    return df,original_ratios,exclude_categories, filtered_ratios

def redistribute_ratios(df, original_ratios, exclude_categories):
    excluded_total_ratio = sum(original_ratios[cat] for cat in exclude_categories)
    top_3_indices = df.nlargest(5, '원래 비율').index
    df.loc[top_3_indices, '원래 비율'] += excluded_total_ratio / 5
    return df


def adjust_weights_with_normalization_calculate_budget(df, filtered_ratios, category, budget):
    decrease_factor = 0.7  # 특정 카테고리의 가중치를 줄이기 위한 감소율
    for cat in category:
        if cat in df['카테고리'].values:
            idx = df[df['카테고리'] == cat].index[0]
            df.at[idx, '가중치'] *= decrease_factor

    # 가중치에 따라 조정된 비율 계산
    df['조정된 비율'] = df['원래 비율'] * df['가중치']
    total_adjusted_ratio = df['조정된 비율'].sum()
    df['최종 비율'] = (df['조정된 비율'] / total_adjusted_ratio) * 100

    # 예산 배분 계산
    budget_distribution = (df.set_index('카테고리')['최종 비율'] / 100 * budget).to_dict()

    return budget_distribution, df

