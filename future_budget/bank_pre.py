import pandas as pd

# 국민은행 전처리
def preprocess_kb(data):
    data = data.iloc[3:, :]
    data.reset_index(drop=True, inplace=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일시', '적요', '출금액', '잔액']]
    data.rename(columns={'적요': '거래내용'}, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    return data

# 농협은행 전처리
def preprocess_nh(data):
    data = data.iloc[6:, 2:]
    data.reset_index(drop=True, inplace=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일시', '거래기록사항', '출금금액', '거래후잔액']]
    data.rename(columns={
        '거래기록사항': '거래내용',
        '출금금액': '출금액',
        '거래후잔액': '잔액'
    }, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['출금액'].notnull()]
    data = data[data['출금액'] > 0]
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    data.reset_index(drop=True, inplace=True)
    return data

# 우리은행 전처리
def preprocess_woori(data):
    data = data.iloc[2:, :].reset_index(drop=True)
    data.columns = data.iloc[0]
    data = data[1:].reset_index(drop=True)
    data = data[['거래일시', '기재내용', '찾으신금액', '거래후 잔액']]
    data.rename(columns={
        '기재내용': '거래내용',
        '찾으신금액': '출금액',
        '거래후 잔액': '잔액'
    }, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    return data

# 카카오뱅크 전처리
def preprocess_kakao(data):
    data = data.iloc[9:, 1:].reset_index(drop=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일시', '거래구분', '거래금액', '거래 후 잔액']]
    data.rename(columns={
        '거래구분': '거래내용',
        '거래금액': '출금액',
        '거래 후 잔액': '잔액'
    }, inplace=True)
    data = data[data['출금액'].astype(str).str.startswith('-')]
    data['출금액'] = data['출금액'].str.replace('-', '', regex=False)
    data['출금액'] = data['출금액'].str.replace(',', '', regex=False).astype(int)
    data['잔액'] = data['잔액'].str.replace(',', '', regex=False).astype(int)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    data.reset_index(drop=True, inplace=True)
    return data

# 케이뱅크 전처리
def preprocess_kbank(data):
    data = data.iloc[2:, :].reset_index(drop=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일시', '적요내용', '출금금액', '잔액']]
    data.rename(columns={
        '적요내용': '거래내용',
        '출금금액': '출금액'
    }, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data.loc[data['출금액'] > 0]
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    return data

# 토스 전처리
def preprocess_toss(data):
    data = data.iloc[8:, 1:].reset_index(drop=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래 일시', '적요', '거래 금액', '거래 후 잔액']]
    data.rename(columns={
        '거래 일시': '거래일시',
        '거래 금액': '출금액',
        '거래 후 잔액': '잔액',
        '적요': '거래내용'
    }, inplace=True)
    data = data[data['출금액'] < 0]
    data['출금액'] = data['출금액'].abs()
    data.reset_index(drop=True, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    return data

# 하나은행 전처리
def preprocess_hana(data):
    data = data.iloc[4:, 0:]
    data = data.drop(data.index[-1])
    data.reset_index(drop=True, inplace=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일시', '적요', '출금액', '잔액']]
    data.rename(columns={'적요': '거래내용'}, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    return data

# MG새마을금고 전처리
def preprocess_mg(data):
    data = data.iloc[10:, :].reset_index(drop=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data[['거래일자', '거래상세', '출금액', '잔액']]
    data.rename(columns={
        '거래상세': '거래내용',
        '거래일자': '거래일시'
    }, inplace=True)
    data['거래일시'] = pd.to_datetime(data['거래일시'])
    data['거래일시'] = data['거래일시'].dt.date
    data = data[data['거래내용'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    data = data.loc[data['출금액'] > 0]
    return data