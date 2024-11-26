# :computer: 미래 가계부: 내일의 돈을 오늘 설계하다
경희대학교 데이터분석/AI 동아리 쿠다 6기에서 진행하는 Data Business 트랙 심화 프로젝트입니다.
<br/>
<br/>

## :one: 프로젝트 소개
> 미래 가계부: 내일의 돈을 오늘 설계하다

![image](https://github.com/user-attachments/assets/04cd9272-3e30-4dcb-957c-2ab4125b35a1)
대학생은 대부분 제한된 예산에서 생활하는 경우가 많고, 사용자마다 일정한 소비 패턴을 보입니다. 수입에 비해서 과소비 경향이 보인다면 어떤 카테고리에서 과소비를 하는지 분석하고 실질적인 해결 방법을 제안해주는 개인화된 지출 관리 추천 시스템을 만들고자 하였습니다!

## :two: 데이터 분석
### 1. 데이터 전처리
- 은행별 전처리
- 카테고리화: chatgptAPI를 통한 거래내역과 관련된 문장 생성 + sentence transformers(ko-sroberta-multitask 모델 사용)
- 거래내역과 가장 유사한 카테고리 도출
### 2. 데이터 분석
> RESULT1: 카테고리별 지출

![image](https://github.com/user-attachments/assets/d3e215bd-c56c-423e-90ca-0eb4251463c9)

> RESULT2: 전체 소비 동향

![image](https://github.com/user-attachments/assets/f00c793d-d473-4bdc-bf3e-b8778e803fdc)

### 3. 데이터 모델링
- LSTM 사용
![image](https://github.com/user-attachments/assets/92d043a9-d715-4f4d-a7f7-c2310ccb1222)
- 모델 성능
  - MAE: 7.63
  - RMSE: 7.85

## :three: 기능 구현
![image](https://github.com/user-attachments/assets/29477b65-038c-4f45-ba55-75d15ab7c8cd)

## :four: 시연 영상
![image](https://github.com/user-attachments/assets/7844f11e-a947-4f06-8900-4030d57dc303)
[https://studio.youtube.com/video/I0gngBUHCps/edit](https://studio.youtube.com/video/I0gngBUHCps/edit)
