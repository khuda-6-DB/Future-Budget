from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_file
import pandas as pd
import os
import calendar
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import json
from datetime import datetime
# 사용자 정의 함수
from file import allowed_file
from bank_pre import preprocess
from visualization import monthly_consumption, monthly_trend_picture, plot_monthly_budget_and_expenses
from category_ratio import prepare_data, redistribute_excluded_categories, load_data, get_top_category
from budget_distribution import calc_original_ratios, adjust_weights_with_normalization_calculate_budget,redistribute_ratios

# 설치된 한글 폰트 경로 설정 (예: 맑은 고딕)
font_path = '/Users/nyeong/Desktop/new/SCDream2.otf'  # Windows
# Linux의 경우: '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = os.urandom(24)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx'}

# 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')

# 두번째 페이지
@app.route('/second_page', methods=['GET', 'POST'])
def second_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        bank_type = request.form['bank_type']

        if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            preprocess_result = preprocess(
                file, bank_type, app.config['UPLOAD_FOLDER'], request.remote_addr
            )
            if isinstance(preprocess_result, dict):
                return jsonify(preprocess_result)
            else:
                return preprocess_result

        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('second_page.html')


# 예산 저장 페이지
money_dict = {}
category_dict = {}

@app.route('/third_page', methods=['GET', 'POST'])
def third_page():
    client_id = request.remote_addr

    if request.method == 'POST':
        budget = request.form['budget']
        categories = request.form.getlist('categories')

        money_dict[client_id] = {'예산': budget}
        category_dict[client_id] = categories

        print(f"money_dict: {money_dict}")
        print(f"category_dict: {category_dict}")

        # JSON 응답 반환
        return jsonify({'message': 'Budget and categories saved successfully'})

    saved_budget = money_dict.get(client_id, {}).get('예산', '')
    saved_categories = category_dict.get(client_id, [])

    return render_template('third_page.html', budget=saved_budget, categories=saved_categories)

# 소비동향보러가기 / 가계부 작성하기
@app.route('/fourth_page')
def fourth_page():
    return render_template('fourth_page.html')

# 과거 페이지
@app.route('/past_page')
def past_page():
    client_id = request.remote_addr
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시'])

    # '거래일시'에서 연도와 월을 추출하고 문자열 리스트로 변환
    year_month_list = df['거래일시'].dt.to_period('M').drop_duplicates().sort_values()
    year_month_list = [str(period) for period in year_month_list]  # 문자열로 변환

    return render_template('past_page.html', year_months=year_month_list)



@app.route('/future_page', methods=['GET', 'POST'])
def future_page():
    client_id = request.remote_addr
    filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_bank.xlsx")
    popup_messages = []

    if os.path.exists(filename_money):
        # Excel 파일 로드
        df = pd.read_excel(filename_money, engine='openpyxl')
        df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
        df = df.dropna(subset=['거래일시'])
        df['출금액'] = pd.to_numeric(df['출금액'], errors='coerce').fillna(0)

        # 주별 날짜 범위 계산 (현재 주)
        today = pd.Timestamp.now().normalize() 
        start_of_week = today - pd.Timedelta(days=today.weekday())  # 이번 주 월요일
        end_of_week = start_of_week + pd.Timedelta(days=6)  # 이번 주 일요일
        start_of_week = pd.to_datetime(start_of_week)
        end_of_week = pd.to_datetime(end_of_week)

        # 주별 데이터 필터링
        filtered_week_df = df[(df['거래일시'] >= start_of_week) & (df['거래일시'] <= end_of_week)]

        # 주별 지출 총액 계산
        total_weekly_expense = filtered_week_df['출금액'].sum()

        # 저장된 월별 예산 가져오기
        total_budget = float(money_dict.get(client_id, {}).get('예산', 0))

        # 주별 예산 계산
        if total_budget > 0:
            days_in_month = pd.Period(today, freq='M').days_in_month
            daily_budget = total_budget / days_in_month
            days_in_week = sum(
                1 for day in pd.date_range(start_of_week, end_of_week)
                if day.month == today.month
            )
            weekly_budget = daily_budget * days_in_week
        else:
            weekly_budget = 0


        # 예산 초과 여부 확인
        if total_weekly_expense > weekly_budget:
            popup_messages.append(
                f"⚠️ 주의: 주별 지출이 예산을 초과했습니다! "
                f"(총 지출: {total_weekly_expense:,}원, 주별 예산: {weekly_budget:,.0f}원)"
            )
        else:
            popup_messages.append(
                f"✅ 잘하고 있습니다! 주별 지출이 예산 내에 있습니다. "
                f"(총 지출: {total_weekly_expense:,}원, 주별 예산: {weekly_budget:,.0f}원)"
            )
        
        # 카테고리별 월별 예산 경고 추가
        df['월'] = df['거래일시'].dt.month
        current_month = today.month
        current_month_data = df[df['월'] == current_month]
        total_monthly_expense = current_month_data['출금액'].sum()
        total_budget = float(money_dict.get(client_id, {}).get('예산', 0))

        # budget_distribution을 사용하여 카테고리별 예산 계산
        category_df, original_ratios, exclude_categories, filtered_ratios = calc_original_ratios(df)
        budget_distribution, adjusted_df = adjust_weights_with_normalization_calculate_budget(
            category_df, filtered_ratios, exclude_categories, total_budget
        )

        # 현재 월 데이터의 카테고리별 지출 합계 계산
        category_monthly_sum = current_month_data.groupby('카테고리')['출금액'].sum()

        # 상위 3개 카테고리 예산 확인
        top_categories = sorted(budget_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        for category, category_budget in top_categories:
            actual_spent = category_monthly_sum.get(category, 0)  # 실제 지출
            if actual_spent > category_budget:
                # 예산 초과 메시지 추가
                popup_messages.append(
                    f"⚠️ {category} 초과! "
                    f"(지출: {actual_spent:,.0f}원, 이번 달 예산: {category_budget:,.0f}원)"
                )
            else:
                # 예산 잔액 메시지 추가
                remaining_budget = category_budget - actual_spent
                popup_messages.append(
                    f"✅ {category} 예산 내 지출 "
                    f"(남은 예산: {remaining_budget:,.0f}원, 지출: {actual_spent:,.0f}원)"
                )

    # future_page.html 템플릿 렌더링
    return render_template('future_page.html', popup_messages=json.dumps(popup_messages))

@app.route('/monthly_expenditure/<year_month>')
def monthly_expenditure(year_month):
    client = request.remote_addr
    result = monthly_consumption(client, font_path, year_month)
    return result

@app.route('/monthly_trend')
def monthly_trend():
    client_id = request.remote_addr
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

    img_url = monthly_trend_picture(client_id, font_path)
    return render_template('monthly_trend.html', img_path=img_url)



@app.route('/add_entry/<date>', methods=['GET', 'POST'])
def add_entry(date):
    client_id = request.remote_addr
    filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_money.xlsx")
    filename_bank = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_bank.xlsx")

    if request.method == 'POST':
        try:
            # 입력 받은 데이터 가져오기
            category = request.form['category']
            amount = int(request.form['amount'])
            action = request.form.get('action', 'submit')  # action 값을 확인 (submit 또는 confirm)

            # 날짜 처리
            date_only = pd.to_datetime(date).date()

            # 데이터프레임 생성
            new_entry = pd.DataFrame({
                '거래일시': [date_only],
                '거래내용': ['입력'],
                '출금액': [amount],
                '잔액': [None],  # 잔액 필드는 비워두거나 필요시 계산
                '카테고리': [category]
            })

            # clientid_money.xlsx 파일 처리
            if os.path.exists(filename_money):
                existing_data_money = pd.read_excel(filename_money, engine='openpyxl')
                updated_data_money = pd.concat([existing_data_money, new_entry], ignore_index=True)
            else:
                updated_data_money = new_entry

            updated_data_money.to_excel(filename_money, index=False, engine='openpyxl')

            # clientid_bank.xlsx 파일 처리
            if os.path.exists(filename_bank):
                existing_data_bank = pd.read_excel(filename_bank, engine='openpyxl')
                updated_data_bank = pd.concat([existing_data_bank, new_entry], ignore_index=True)
            else:
                updated_data_bank = new_entry

            updated_data_bank.to_excel(filename_bank, index=False, engine='openpyxl')

            # JSON 응답 반환 (AJAX 요청 처리)
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': '데이터가 성공적으로 저장되었습니다.'}), 200

        except Exception as e:
            # 오류 발생 시 JSON 응답 반환
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'}), 500

            return render_template('error.html', message=f"오류 발생: {str(e)}")
    

    # 추가 1. 기존 데이터를 로드하여 사용자에게 표시
    client_id = request.remote_addr
    filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_money.xlsx")
    entries = []
    total_amount = 0

    # 파일에서 데이터 로드
    if os.path.exists(filename_money):
        existing_data_money = pd.read_excel(filename_money, engine='openpyxl')
        existing_data_money['거래일시'] = pd.to_datetime(existing_data_money['거래일시']).dt.date

        # 특정 날짜의 데이터 필터링
        filtered_data = existing_data_money[existing_data_money['거래일시'] == pd.to_datetime(date).date()]
        entries = filtered_data.to_dict('records')

        # 총 출금액 계산
        total_amount = filtered_data['출금액'].sum()

    return render_template('entry_form.html', date=date, entries=entries, total_amount=total_amount)


@app.route('/weekly_expenditure/<week_start>/<week_end>')
def weekly_expenditure(week_start, week_end):
    # 한글 폰트 설정 (예: 맑은 고딕)
    font_path = 'SCDream2.otf'  # Windows 환경
    fontprop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=fontprop.get_name())
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

    client_id = request.remote_addr
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

    # 데이터 읽기 및 전처리
    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시']).copy()  # .copy()로 경고 방지
    df['출금액'] = pd.to_numeric(df['출금액'], errors='coerce').fillna(0)

    # 주 시작일과 종료일을 datetime 형식으로 변환
    week_start_date = pd.to_datetime(week_start) + pd.Timedelta(days=1)
    week_end_date = pd.to_datetime(week_end) + pd.Timedelta(days=1)
    week_start = (pd.to_datetime(week_start) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    week_end = (pd.to_datetime(week_end) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 주별 데이터 필터링
    filtered_week_df = df[(df['거래일시'] >= week_start_date) & (df['거래일시'] <= week_end_date)]

    if filtered_week_df.empty:
        return f"No data for the week from {week_start} to {week_end}"

    # 카테고리별 지출 계산
    weekly_expense = filtered_week_df.groupby('카테고리')['출금액'].sum()

    # 시각화 준비
    colors = plt.cm.tab20(np.linspace(0, 1, len(weekly_expense)))

    # 상위 3개 항목 및 '기타' 항목 계산
    top_3 = weekly_expense.nlargest(3)
    others = weekly_expense.sum() - top_3.sum()
    if others > 0:
        category_expense = pd.concat([top_3, pd.Series({'기타': others})])
    else:
        category_expense = top_3

    # 이미지 저장 경로 설정
    img_filename = f"{client_id}_{week_start}_to_{week_end}_chart.png"
    img_path = os.path.join('static', img_filename)

    # 파이차트 생성
    plt.figure(figsize=(8, 8))
    plt.pie(
        category_expense,
        labels=category_expense.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors[:len(category_expense)]
    )
    plt.title(f"지출 비율 ({week_start} ~ {week_end})", fontproperties=fontprop, fontsize=16)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    img_url = f"/static/{img_filename}"
    return render_template('weekly_expenditure.html', img_path=img_url)

# 추가 2. 입력한 가계부 삭제 기능
@app.route('/delete_current_entry/<int:entry_index>', methods=['POST'])
def delete_current_entry(entry_index):
    client_id = request.remote_addr
    filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_money.xlsx")
    date = request.form.get('date')  # 폼 데이터에서 날짜 가져오기

    if os.path.exists(filename_money):
        existing_data_money = pd.read_excel(filename_money, engine='openpyxl')

        # 선택한 인덱스의 데이터 제외
        updated_data = existing_data_money.drop(index=entry_index)

        # 업데이트된 데이터를 다시 저장
        updated_data.to_excel(filename_money, index=False, engine='openpyxl')

    # 삭제 후 다시 해당 날짜의 entry_form 페이지로 리디렉션
    return redirect(url_for('add_entry', date=date))

# 추가 3. 가계부 초기화
@app.route('/clear_data', methods=['POST'])
def clear_data():
    client_id = request.remote_addr
    filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_money.xlsx")
    filename_bank = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_bank.xlsx")

    deleted_files = []
    for filename in [filename_money, filename_bank]:
        if os.path.exists(filename):
            os.remove(filename)
            deleted_files.append(filename)
        else:
            print(f"File not found: {filename}")
            
    return redirect(url_for('future_page'))
    
@app.route('/mbti_page', methods=['GET', 'POST'])
def mbti_page():
    client_id = request.remote_addr
    processed_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_bank.xlsx")

    # 파일 존재 여부 확인 및 처리
    if os.path.exists(processed_file_path):
        data = load_data(processed_file_path)  # 데이터 로드
        if data is not None and not data.empty:
            top_category = get_top_category(data)  # 최상위 카테고리 계산
            session['top_category'] = top_category
        else:
            top_category = "데이터를 읽는 중 오류 발생"
    else:
        top_category = "업로드된 데이터 없음"

    return render_template('mbti_page.html', top_category=top_category)

# Flask 라우트 추가
@app.route('/future_budget_visualization', methods=['POST'])
def future_budget_visualization():
    client_id = request.remote_addr
    current_month = datetime.now().month
    current_year = datetime.now().year
    file_path = f"./uploads/{client_id}_bank.xlsx"
    current_month_str = f"{current_year}-{current_month:02d}"

    if not os.path.exists(file_path):
        return "No data file available."

    # 데이터 로드 및 전처리
    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시'])
    df['출금액'] = pd.to_numeric(df['출금액'], errors='coerce').fillna(0)
    df['월'] = df['거래일시'].dt.to_period('M')
    monthly_expense_data = df.copy()

    
    # 지난달들을 기준으로 비율 계산
    df = df[df['월'] != current_month_str]
    df, original_ratios, exclude_categories, filtered_ratios = calc_original_ratios(df)
    df = redistribute_ratios(df, original_ratios, exclude_categories)
    budget_distribution, df = adjust_weights_with_normalization_calculate_budget(df,filtered_ratios,category_dict[client_id], float(money_dict[client_id]['예산']))

    # 현재 월 데이터 추출 및 카테고리 정보 추가
    # 기존 데이터프레임 처리
    monthly_expense_data = monthly_expense_data.groupby(['월', '카테고리'])['출금액'].sum().unstack(fill_value=0)
    monthly_expense_data = monthly_expense_data.reset_index()
    monthly_expense_data['월'] = monthly_expense_data['월'].astype(str)

    # original_ratios의 카테고리 순서대로 재정렬
    ordered_columns = ['월'] + list(original_ratios.keys())
    monthly_expense_data = monthly_expense_data.reindex(columns=ordered_columns, fill_value=0)
    if f"{current_year}-{current_month:02d}" in monthly_expense_data['월'].values:
        current_month_row = monthly_expense_data[monthly_expense_data['월'] == f"{current_year}-{current_month:02d}"].iloc[0]

    # original_ratios에 값이 있으면 넣고, 없으면 0으로 초기화
        current_month_data = pd.DataFrame({
            '카테고리': list(original_ratios.keys()),
            '지출액': [current_month_row.get(cat, 0) for cat in original_ratios.keys()]
        })
    else:
    # original_ratios에 기반한 빈 데이터프레임 생성
        current_month_data = pd.DataFrame({
            '카테고리': list(original_ratios.keys()),
            '지출액': [0] * len(original_ratios)
        })


    img_path = plot_monthly_budget_and_expenses(current_month_data,budget_distribution,exclude_categories, font_path, client_id)
    return jsonify({"img_path": img_path})


if __name__ == '__main__':
    app.run(debug=True)