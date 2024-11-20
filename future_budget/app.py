from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_file
import pandas as pd
from werkzeug.utils import secure_filename
import os
import calendar
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
from category_ratio import get_top_category


# Flask app creation
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'

# UPLOAD_FOLDER configuration
app.config['UPLOAD_FOLDER'] = './uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx'}

# Import user-defined functions
from bank_pre import preprocess_kb, preprocess_nh, preprocess_woori, preprocess_kakao, preprocess_kbank, preprocess_toss, preprocess_hana, preprocess_mg
from category_mapping import apply_category_mapping

# Allowed file extensions verification
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Read transaction file from the form
def read_transaction_file(file_path):
    try:
        file_extension = file_path.split('.')[-1].lower()
        if file_extension == 'xls':
            data = pd.read_excel(file_path, engine="xlrd")
        elif file_extension == 'xlsx':
            data = pd.read_excel(file_path, engine="openpyxl")
        else:
            raise ValueError("Unsupported file format. Please upload a .xls or .xlsx file.")
        return data
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None
def plot_monthly_trend(df, year_month, client_id):
    # 설치된 한글 폰트 경로 설정 (예: 맑은 고딕)
    font_path = 'C:/Windows/Fonts/malgun.ttf'  # Windows
    # Linux의 경우: '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

    fontprop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=fontprop.get_name())
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

    # 연, 월을 추출하여 해당 달의 데이터를 필터링
    year, month = map(int, year_month.split('-'))
    filtered_df = df[(df['거래일시'].dt.year == year) & (df['거래일시'].dt.month == month)]

    if filtered_df.empty:
        return None, f"No data for {year_month}"

    # 날짜별 총 출금액 계산
    filtered_df['출금액'] = pd.to_numeric(filtered_df['출금액'], errors='coerce').fillna(0)
    daily_expense = filtered_df.groupby(filtered_df['거래일시'].dt.date)['출금액'].sum()

    # 선 그래프 생성 및 저장
    img_filename = f"{client_id}_{year_month}_trend_chart.png"
    img_path = os.path.join('static', img_filename)

    plt.figure(figsize=(12, 6))
    plt.plot(daily_expense.index, daily_expense.values, marker='o', linestyle='-', color='b')
    plt.title(f"{year_month} 월별 지출 동향", fontproperties=fontprop, fontsize=16)
    plt.xlabel("날짜", fontproperties=fontprop)
    plt.ylabel("출금액 (KRW)", fontproperties=fontprop)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    return img_path, None

# Data processing based on bank type
def process_data(data, bank_type):
    if bank_type == "국민은행":
        processed_data = preprocess_kb(data)
    elif bank_type == "농협은행":
        processed_data = preprocess_nh(data)
    elif bank_type == "우리은행":
        processed_data = preprocess_woori(data)
    elif bank_type == "카카오뱅크":
        processed_data = preprocess_kakao(data)
    elif bank_type == "케이뱅크":
        processed_data = preprocess_kbank(data)
    elif bank_type == "토스":
        processed_data = preprocess_toss(data)
    elif bank_type == "하나은행":
        processed_data = preprocess_hana(data)
    elif bank_type == "MG새마을금고":
        processed_data = preprocess_mg(data)
    else:
        raise ValueError("Unsupported bank type.")

    categorized_data = apply_category_mapping(processed_data)
    output_filename = f"processed_{bank_type}.xlsx"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    categorized_data.to_excel(output_path, index=False)
    print(f"Processed data saved at {output_path}.")
    return categorized_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/second_page', methods=['GET', 'POST'])
def second_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        bank_type = request.form['bank_type']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            data = read_transaction_file(file_path)
            if data is not None:
                try:
                    result_data = process_data(data, bank_type)
                    clientid_bank = f"{request.remote_addr}_bank"
                    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{clientid_bank}.xlsx")

                    if os.path.exists(output_path):
                        existing_data = pd.read_excel(output_path, engine="openpyxl")
                        merged_data = pd.concat([existing_data, result_data], ignore_index=True)
                    else:
                        merged_data = result_data

                    merged_data.to_excel(output_path, index=False)
                    print(f"Processed data saved at {output_path}.")

                    # 성공적인 처리 후, 파일이 업로드되었음을 알리고 다음 페이지로 리디렉션할 URL을 포함한 JSON 응답 반환
                    return jsonify({
                        'message': 'File uploaded and processed successfully',
                        'redirect_url': url_for('third_page')  # third_page로 리디렉션
                    })
                except Exception as e:
                    print(f"Error: {e}")
                    return jsonify({'error': 'An error occurred. Check the logs.'})
            else:
                return jsonify({'error': 'Unable to read the file.'})

    return render_template('second_page.html')

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


@app.route('/fourth_page')
def fourth_page():
    return render_template('fourth_page.html')

    

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
    popup_message = ""

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
            # 현재 월의 총 일수 계산
            days_in_month = pd.Period(today, freq='M').days_in_month

            # 일별 예산 계산
            daily_budget = total_budget / days_in_month

            # 이번 주에 해당하는 일수 계산 (월 경계 고려)
            days_in_week = sum(
                1 for day in pd.date_range(start_of_week, end_of_week)
                if day.month == today.month
            )

            # 주별 예산 계산
            weekly_budget = daily_budget * days_in_week
        else:
            weekly_budget = 0


        # 예산 초과 여부 확인
        if total_weekly_expense > weekly_budget:
            popup_message = (
                f"주의: 주별 지출이 예산을 초과했습니다! "
                f"(총 지출: {total_weekly_expense}원, 주별 예산: {weekly_budget:.0f}원)"
            )
        else:
            popup_message = (
                f"잘하고 있습니다! 주별 지출이 예산 내에 있습니다. "
                f"(총 지출: {total_weekly_expense}원, 주별 예산: {weekly_budget:.0f}원)"
            )

    # future_page.html 템플릿 렌더링
    return render_template('future_page.html', popup_message=popup_message)


@app.route('/monthly_expenditure/<year_month>')
def monthly_expenditure(year_month):

    # 설치된 한글 폰트 경로 설정 (예: 맑은 고딕)
    font_path = 'SCDream2.otf'  # Windows
    # Linux의 경우: '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

    fontprop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=fontprop.get_name())

    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False
    client_id = request.remote_addr
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

@app.route('/monthly_trend')
def monthly_trend():
    client_id = request.remote_addr
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

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
    return render_template('monthly_trend.html', img_path=img_url)



@app.route('/add_entry/<date>', methods=['GET', 'POST'])
def add_entry(date):
    if request.method == 'POST':
        # 입력 받은 데이터 가져오기
        category = request.form['category']
        amount = int(request.form['amount'])
        client_id = request.remote_addr
        filename_money = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_money.xlsx")
        filename_bank = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_bank.xlsx")

        # 시간 제거 후 날짜 처리
        date_only = pd.to_datetime(date).date()

        # 데이터프레임 생성
        new_entry = pd.DataFrame({
            '거래일시': [date_only],  # 시간 없이 날짜만 저장
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

        # future_page로 리디렉션
        return redirect(url_for('future_page'))
    
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
    print(week_start)
    print(week_start_date)
    print(week_end_date)
    
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

    if deleted_files:
        print(f"Deleted files: {deleted_files}")
        return "데이터가 삭제되었습니다.", 200
    else:
        return "삭제할 데이터가 없습니다.", 404
    
@app.route('/mbti_page', methods=['GET', 'POST'])
def mbti_page():
    from category_ratio import get_top_category
    top_category = session.get('top_category')

    if request.method == 'POST':
        return render_template('mbti_page.html', top_category=top_category)

    return render_template('mbti_page.html', top_category=top_category)
    
# Flask 라우트 추가
@app.route('/future_budget_visualization', methods=['POST'])
def future_budget_visualization():
    client_id = request.remote_addr
    current_month = datetime.now().month
    current_year = datetime.now().year
    file_path = f"./uploads/{client_id}_bank.xlsx"

    if not os.path.exists(file_path):
        return "No data file available."

    # 데이터 로드 및 전처리
    df = pd.read_excel(file_path, engine="openpyxl")
    df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
    df = df.dropna(subset=['거래일시'])
    df['출금액'] = pd.to_numeric(df['출금액'], errors='coerce').fillna(0)
    df['월'] = df['거래일시'].dt.to_period('M')

    # 카테고리별 비율 계산
    monthly_expense_data = df.groupby(['월', '카테고리'])['출금액'].sum().unstack(fill_value=0)
    monthly_expense_data = monthly_expense_data.reset_index()
    monthly_expense_data['월'] = monthly_expense_data['월'].astype(str)

    # 모든 데이터 문자열로 변환 후 숫자형으로 변환 시도
    for col in monthly_expense_data.columns[1:]:
        monthly_expense_data[col] = monthly_expense_data[col].apply(lambda x: pd.to_numeric(str(x).replace(',', ''), errors='coerce'))
    output_filename = f"monthly_expense_data.xlsx"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    monthly_expense_data.to_excel(output_path, index=False)
    # 숫자형 컬럼만 선택하여 합계 계산
    category_total_sum = monthly_expense_data.iloc[:, 1:].sum()
    print('1')
    # 비율 계산
    category_ratios = (category_total_sum / category_total_sum.sum()) * 100
    original_ratios = category_ratios.to_dict()

    # 현재 월 데이터 추출 및 카테고리 정보 추가
    if f"{current_year}-{current_month:02d}" in monthly_expense_data['월'].values:
        current_month_data = monthly_expense_data[monthly_expense_data['월'] == f"{current_year}-{current_month:02d}"].drop(columns=['월']).melt(var_name='카테고리', value_name='지출액')
    else:
        current_month_data = pd.DataFrame(columns=['카테고리', '지출액'])

    # current_month_data 파일로 저장
    output_filename = f"current_month_data.xlsx"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    current_month_data.to_excel(output_path, index=False)
    # 카테고리별 지출 비율 계산
    # 현재 연도와 월
    current_month_str = f"{current_year}-{current_month:02d}"

    # 현재 달을 제외한 데이터프레임 생성
    filtered_expense_data = monthly_expense_data[monthly_expense_data['월'] != current_month_str]

    # 월 열을 제외하고 나머지 열을 모두 숫자형으로 변환
    filtered_expense_data.iloc[:, 1:] = filtered_expense_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)
    # 숫자형 열만 선택하여 합계 계산
    category_total_sum = filtered_expense_data.drop(columns=['월']).select_dtypes(include=[np.number]).sum()

    category_ratios = (category_total_sum / category_total_sum.sum()) * 100
    original_ratios = category_ratios.to_dict()

    # 가중치 조정
    exclude_categories = ["간편 결제", "이체", "기타"]
    filtered_ratios = {k: v for k, v in original_ratios.items() if k not in exclude_categories}
    print("\nflitered_ratios",filtered_ratios)
    categories = list(filtered_ratios.keys())
    # ['식비','카페',,,,]
    weights = [1.0] * len(categories)
    df_ratios = pd.DataFrame({'카테고리': categories, '원래 비율': list(filtered_ratios.values()), '가중치': weights})
    excluded_total_ratio = sum(original_ratios[cat] for cat in exclude_categories)
    top_3_indices = df_ratios.nlargest(5, '원래 비율').index
    df_ratios.loc[top_3_indices, '원래 비율'] += excluded_total_ratio / 5

    # 선택된 카테고리 가져오기
    selected_categories = [categories.index(cat) for cat in category_dict[client_id] if cat in categories]
    print(selected_categories)
    # [11] -> 편의점이라 11

    def adjust_weights_with_normalization():
        decrease_factor = 0.7
        for idx in selected_categories:
            df_ratios.at[idx, '가중치'] *= decrease_factor

        df_ratios['조정된 비율'] = df_ratios['원래 비율'] * df_ratios['가중치']
        total_adjusted_ratio = df_ratios['조정된 비율'].sum()
        df_ratios['최종 비율'] = (df_ratios['조정된 비율'] / total_adjusted_ratio) * 100

    adjust_weights_with_normalization()

    budget = float(money_dict[client_id]['예산'])
    budget_distribution = (df_ratios['최종 비율'] / 100 * budget).to_dict()


    def plot_monthly_budget_and_expenses():
        monthly_expense = current_month_data.to_dict()

        # 제외된 카테고리 제거
        filtered_categories = {idx: cat for idx, cat in monthly_expense['카테고리'].items() if cat not in exclude_categories}
        filtered_expenses = {idx: expense for idx, expense in monthly_expense['지출액'].items() if idx in filtered_categories}

        # filtered_expense 딕셔너리 생성
        filtered_expense = {
            '카테고리': filtered_categories,
            '지출액': filtered_expenses
        }

        # 인덱스를 0부터 다시 할당
        monthly_expense = {
            '카테고리': {new_idx: cat for new_idx, (old_idx, cat) in enumerate(filtered_expense['카테고리'].items())},
            '지출액': {new_idx: filtered_expense['지출액'][old_idx] for new_idx, old_idx in enumerate(filtered_expense['지출액'].keys())}
        }
        categories_name = list(monthly_expense['카테고리'].values())
        categories = list(budget_distribution.keys())
        print(categories)
        print('\n예산 확인: ',budget_distribution)
        expense_values = [monthly_expense['지출액'].get(cat, 0) for cat in categories]
        budget_values = [budget_distribution[cat] for cat in categories]
        print("\n카테고리확인지출: ",monthly_expense)
        remaining_budget = [budget_distribution[cat] - monthly_expense['지출액'].get(cat, 0) for cat in categories]
        print(categories_name)

        fig, ax = plt.subplots(figsize=(15, 10))
        bars_expense = ax.bar(categories, expense_values, color='darkblue', label='지출')
        bars_remaining = ax.bar(categories, remaining_budget, color='lightblue', alpha=0.7, label='남은 예산', bottom=expense_values)

        font_path = 'SCDream2.otf'
        fontprop = fm.FontProperties(fname=font_path)
        ax.set_ylabel('금액 (원)', fontproperties=fontprop)
        ax.set_xlabel('카테고리', fontproperties=fontprop)
        ax.set_title(f'{current_year}-{current_month:02d} 월별 카테고리별 지출 및 남은 예산', fontproperties=fontprop)
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
            print(text_position)
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

    img_path = plot_monthly_budget_and_expenses()
    return render_template('future_budget_visualization.html', img_path=img_path)


if __name__ == '__main__':
    app.run(debug=True)