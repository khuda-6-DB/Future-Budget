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

<img src="https://github.com/user-attachments/assets/d3e215bd-c56c-423e-90ca-0eb4251463c9" width="70%" alt="카테고리별 지출">

> RESULT2: 전체 소비 동향

<img src="https://github.com/user-attachments/assets/d2fdf07e-30f4-40a5-9e44-47663cdb904b" width="70%" alt="전체 소비 동향">

### 3. 데이터 모델링
- LSTM 사용
<img src="https://github.com/user-attachments/assets/92d043a9-d715-4f4d-a7f7-c2310ccb1222" width="70%" alt="LSTM 사용">

- 모델 성능
  - MAE: 7.63
  - RMSE: 7.85


## :three: 기능 구현
![image](https://github.com/user-attachments/assets/29477b65-038c-4f45-ba55-75d15ab7c8cd)

  
## :four: 시연 영상
<img src="https://github.com/user-attachments/assets/7844f11e-a947-4f06-8900-4030d57dc303" width="50%" alt="이미지 1">
<img src="https://github.com/user-attachments/assets/2a458534-ba3d-4ff1-b583-394f3d024e14" width="50%" alt="이미지 2">

[https://studio.youtube.com/video/I0gngBUHCps/edit](https://studio.youtube.com/video/I0gngBUHCps/edit)


## :five: 팀원 소개
<table>
  <tbody>
    <tr>
      <!-- 최소영 -->
      <td align="center">
        <a href="https://github.com/gitchlthdud">
          <img src="https://avatars.githubusercontent.com/u/160228065?s=400&u=9f5549fa482168dde89d7a41f3155b1d009ede0b&v=4" width="100px" alt="FE 팀장"/><br />
          <sub><b>최소영</b></sub>
        </a>
      </td>
      <!-- 이제희 -->
      <td align="center">
        <a href="https://github.com/pinkkj">
          <img src="https://avatars.githubusercontent.com/u/103947888?v=4" width="100px" alt="FE 팀원 1"/><br />
          <sub><b>이제희</b></sub>
        </a>
      </td>
      <!-- 이준영 -->
      <td align="center">
        <a href="https://github.com/junyeong-khu">
          <img src="https://avatars.githubusercontent.com/u/175942581?v=4" width="100px" alt="FE 팀원 2"/><br />
          <sub><b>이준영</b></sub>
        </a>
      </td>
      <!-- 허채은 -->
      <td align="center">
        <a href="https://github.com/chereunii](https://github.com/chereunii">
          <img src="https://avatars.githubusercontent.com/u/174696900?v=4" width="100px" alt="FE 팀원 3"/><br />
          <sub><b>허채은</b></sub>
        </a>
      </td>
    </tr>
  </tbody>
</table>


