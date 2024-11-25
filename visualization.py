import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from flask import render_template

# 과거 월별 소비량
def monthly_consumption(client, font, year_month):
    
    # 설치된 한글 폰트 경로 설정 (예: 맑은 고딕)
    font_path = font  # Windows
    # Linux의 경우: '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

    fontprop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=fontprop.get_name())

    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False
    client_id = client
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시'])

    # year_month를 기반으로 데이터 필터링
    year, month = map(int, year_month.split('-'))
    filtered_df = df[(df['거래일시'].dt.year == year) & (df['거래일시'].dt.month == month)]

    if filtered_df.empty:
        return f"No data for {year_month}"

    # 카테고리별 지출 시각화
    filtered_df['출금액'] = pd.to_numeric(filtered_df['출금액'], errors='coerce').fillna(0)
    monthly_expense = filtered_df.groupby('카테고리')['출금액'].sum()

    # 시각화
    colors = ['#FFB6C1', '#FFDAB9', '#E6E6FA', '#B0E0E6', '#ADD8E6', '#98FB98',
              '#FFE4B5', '#FFD700', '#FFC0CB', '#DDA0DD', '#AFEEEE', '#D3D3D3']

    if not monthly_expense.empty:
        top_3 = monthly_expense.nlargest(3)
        others = monthly_expense.sum() - top_3.sum()
        category_expense = pd.concat([top_3, pd.Series({'기타': others})])

        # 이미지 저장 경로
        img_filename = f"{client_id}_{year_month}_chart.png"
        img_path = os.path.join('static', img_filename)  # 실제 파일 저장 경로

        # 파이차트 생성
        plt.figure(figsize=(8, 8))
        plt.pie(
            category_expense,
            labels=category_expense.index,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors[:len(category_expense)]
        )
        plt.title(f"{year_month} 카테고리별 지출 비율")
        plt.tight_layout()
        plt.savefig(img_path)  # 이미지 저장
        plt.close()
        img_url = f"/static/{img_filename}"
        return render_template('monthly_expenditure.html', img_path=img_url)
    else:
        return f"No expenditure data for {year_month}"

# 모든 월 추세
def monthly_trend_picture(client_id,font):
    # 설치된 한글 폰트 경로 설정 (예: 맑은 고딕)
    font_path = font  # Windows
    # Linux의 경우: '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

    fontprop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=fontprop.get_name())

    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False
    file_path = f"./uploads/{client_id}_bank.xlsx"
    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시'])
    df['출금액'] = pd.to_numeric(df['출금액'], errors='coerce').fillna(0)
    df['year_month'] = df['거래일시'].dt.to_period('M')

    # 월별 총 출금액 계산
    monthly_expense = df.groupby('year_month')['출금액'].sum()

    # 선 그래프 생성 및 저장
    img_filename = f"{client_id}_all_months_trend_chart.png"
    img_path = os.path.join('static', img_filename)

    plt.figure(figsize=(12, 6))
    plt.plot(monthly_expense.index.astype(str), monthly_expense.values, marker='o', linestyle='-', color='b')
    plt.title("월별 소비량 변화")
    plt.xlabel("월")
    plt.ylabel("출금액 (KRW)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    img_url = f"/static/{img_filename}"
    return img_url

def plot_monthly_budget_and_expenses(current_month_data,budget_distribution, exclude_categories, font, client_id):

    # {카테고리:{}, 지출액:{}} 만들기 -> 이번달
    monthly_expense = current_month_data.to_dict()
    filtered_categories = {idx: cat for idx, cat in monthly_expense['카테고리'].items() if cat not in exclude_categories}
    filtered_expenses = {idx: expense for idx, expense in monthly_expense['지출액'].items() if idx in filtered_categories}
    filtered_expense = {
        '카테고리': filtered_categories,
        '지출액': filtered_expenses
    }
    monthly_expense = {
        '카테고리': {new_idx: cat for new_idx, (old_idx, cat) in enumerate(filtered_expense['카테고리'].items())},
        '지출액': {new_idx: filtered_expense['지출액'][old_idx] for new_idx, old_idx in enumerate(filtered_expense['지출액'].keys())}
    }

    categories_name = list(monthly_expense['카테고리'].values())
    categories = list(budget_distribution.keys())

    # 역매핑 딕셔너리 생성
    category_to_number = {v: k for k, v in filtered_categories.items()}

    # categories 리스트를 숫자로 변환
    categories_numbers = [category_to_number[cat] for cat in categories]
    expense_values = [monthly_expense['지출액'].get(cat, 0) for cat in categories_numbers]

    print(expense_values)
    budget_values = [budget_distribution[cat] for cat in categories]
    remaining_budget = [budget_distribution[cat] - monthly_expense['지출액'].get(cat, 0) for cat in categories]

    fig, ax = plt.subplots(figsize=(15, 10))
    bars_expense = ax.bar(categories, expense_values, color='darkblue', label='지출')
    bars_remaining = ax.bar(categories, remaining_budget, color='lightblue', alpha=0.7, label='남은 예산', bottom=expense_values)

    font_path = font
    fontprop = fm.FontProperties(fname=font_path)
    ax.set_ylabel('금액 (원)', fontproperties=fontprop)
    ax.set_xlabel('카테고리', fontproperties=fontprop)
    ax.set_title(f'카테고리별 지출 및 남은 예산', fontproperties=fontprop)
    ax.legend(prop=fontprop)
    ax.margins(x=0.01)
    ax.set_xticks(range(len(categories_name)))  # x축 틱의 개수를 카테고리 수에 맞춤
    ax.set_xticklabels(categories_name, fontproperties=fontprop)

    # 각 바에 지출, 예산, 남은 돈을 한 박스에 표시
    for i in range(len(categories)):
        expense = expense_values[i]
        budget = budget_values[i]
        remaining = remaining_budget[i]
        text_position = budget + expense if budget + expense < max(budget, expense) else max(budget, expense)
        
        # 텍스트 박스 내용 생성
        text = f'예산: {budget:,.0f}원\n지출: {expense:,.0f}원\n남은 돈: {remaining:,.0f}원'
        #height_offset = 200 if text_position == budget+expense else 10
        height_offset = 10
        # 박스에 텍스트 추가
        ax.annotate(
            text,
            (i, text_position),
            textcoords="offset points",
            xytext=(0, height_offset),
            ha='center',
            bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='white'),
            fontproperties=fontprop,
            fontsize=8
        )

    plt.tight_layout(pad=2.0)
    img_path = f'static/{client_id}_monthly_budget.png'
    plt.savefig(img_path)
    plt.close()
    return img_path