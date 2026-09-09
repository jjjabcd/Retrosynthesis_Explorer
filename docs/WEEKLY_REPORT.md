# Personal

## Side Project

### Retrosynthesis Explorer

AiZynthFinder와 RDKit을 활용한 로컬 역합성 GUI를 구현했다. Conda 환경에서 실행하며 브라우저의 `localhost`로 사용한다.

#### 1. Target molecule

![Target molecule input and preview](images/accessibility-scores.png)

- SMILES 입력 및 2D 분자구조 미리보기
- 탐색 시간, 반복 횟수, 최대 단계, 탐색·반환 경로 수 설정
- RDKit 물리화학 특성과 SAScore, RAScore 표시

#### 2. Synthetic routes

![Synthetic route list](images/workspace.png)

- 역합성 결과를 점수순 경로 목록으로 표시
- 반응 단계 수, 출발물질 수, State score, Solved 상태 제공
- 경로를 선택하면 별도의 상세 화면으로 이동

#### 3. Route details

![Retrosynthetic route](images/selected-route.png)

- 선택한 경로를 분자구조가 포함된 retrosynthetic route로 시각화
- 목표 분자, 중간체, 출발물질에 노드 ID를 부여해 특성 표와 연결
- 각 분자의 분자식, 분자량, cLogP, TPSA 등 계산 특성 표시

#### 4. Export

![Export options](images/export-dialog.png)

- 전체 경로를 PNG로 저장
- 개별 분자를 PNG 또는 SVG로 저장
- 모든 분자 이미지를 ZIP으로 저장
- 분자 특성을 CSV 또는 JSON으로 저장

## Resume

- 이번 주 업데이트 없음

## Homepage

- 이번 주 업데이트 없음
