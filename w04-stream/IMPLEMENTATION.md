# Week 4 구현과 재현 방법

세 과제는 Python 표준 라이브러리만 사용한다. 알고리즘을 제공하는 외부 라이브러리는 호출하지 않는다. `bench.py`, `test_tasks.py`, 루트 `check.py`는 원본 그대로다.

## Task 1

Bloom filter는 bytearray에 bit를 packing하고, SHAKE-256의 64-bit pseudorandom output lane을 hash별 위치로 사용한다. 같은 입력/seed는 같은 위치를 만들며 삭제 연산이 없다. 기대 오탐률은 측정값과 무관하게 `(1-exp(-kn/m))^k`로 계산한다.

FM은 각 항목을 64개의 64-bit hash lane으로 보내 trailing-zero 최대값을 저장한다. 각 lane을 하나씩 검사하는 스칼라 알고리즘과 동일한 packed 정수 zero test를 사용해 Python loop 비용을 줄였다. `test_regressions.py`에서 독립적인 스칼라 oracle 및 0/최상위 bit 경계를 비교한다. 이 알고리즘은 스트림 항목을 저장하지 않는다.

Combiner는 8개씩 묶어 평균 R을 계산하고, group 평균의 중앙값을 취한 뒤 지수화한다. 이는 group 안에서 `2^R`의 기하평균에 해당한다. `E[max R] ≈ log2(D) + gamma/ln(2) - 1/2`의 점근적 offset을 빼므로 거대한 `2^R` outlier를 직접 평균내지 않는다. 이 보정은 maximum-R 추정기용이며, bitmap의 첫 0 위치에 사용하는 0.77351 상수를 혼용하지 않는다. 모든 seed와 크기에 대해 같은 규칙을 사용한다. 비교 실험과 24개 seed/크기 검증은 `out/sketch-analysis.json`에 기록한다.

Reservoir는 Algorithm R: i번째 항목에서 0..i-1의 정수를 뽑고 k보다 작으면 교체한다. 최종 n을 미리 알거나 스트림을 다시 읽을 필요가 없다.

## Task 2

이 과제의 메모리 곡선은 실제 학생 PC를 측정해야 하므로 Windows 로컬에서 수행했다. `limits.json`의 CPU·RAM·실행 중 프로그램 기록을 함께 제출한다. 시간과 memory peak 모두 tracemalloc이 활성화된 실행에서 측정했다. Peak은 추적된 Python 할당이며 프로세스 RSS 전체와 다르다.

완료된 크기: 100,000 / 400,000 / 1,600,000 / 6,400,000 (64배).
추가 큰 실행은 시간·추적 메모리 경계를 지정해 시스템을 과도하게 점유하지 않도록 중단할 수 있다. 중단된 실행은 partial 결과로 표시하며 완료된 truth나 OOM으로 표현하지 않는다.

```bash
cd w04-stream
python task2_limits.py --sizes 100000,400000,1600000,6400000
python task2_limits.py --sizes 25000000 --exact-time-limit 60 --max-exact-mib 768
```

## Task 3

80,000비트 / 8,000항목에서 k* = 10 ln2 ≈ 6.93이므로 k=7을 사용한다. hash 함수와 seed는 질의 데이터에 맞춰 튜닝하지 않았다. filter는 `__slots__`로 인스턴스 dictionary를 제거하고, 하나의 bytearray 안에 seed 8바이트와 packed bitset을 저장한다.

`memory_bits()`는 인스턴스와 bytearray의 실제 `sys.getsizeof`를 합산한다. 따라서 seed와 Python container header도 포함한다. 입력 스트림/benchmark가 가진 항목, 공통 interpreter 및 공유 코드, 일시적인 hash 계산 작업공간은 retained 필터 상태와 별도로 구분한다. 숨겨진 exact set이나 항목 cache는 없다. 추가 memory 검증에서 삽입 전후의 retained 크기가 변하지 않음을 확인한다.

80,000비트 전체가 membership bit인 이상적인 Bloom 모형의 floor는 `exp(-10(ln2)^2) ≈ 0.819%`다. Python header와 seed를 제외하면 유효 bit는 더 적으므로 실제 기대 오탐률은 약간 높아진다. 이것은 표준 Bloom 모형에서 k를 최적화한 예측값이며 모든 membership 자료구조에 대한 보편적인 정보론적 하한을 주장하지 않는다.

주의: baseline은 `bytearray(n_bits)`를 할당해 실제로는 논리 bit마다 1바이트를 사용하지만, 제공된 `memory_bits()`는 80,000 logical bits만 보고한다. 원본 baseline/harness는 수정하지 않았다. 개선 filter는 이 accounting 문제를 이용해 예산을 늘리지 않고 실제 retained 메모리를 10,000바이트 안에 유지한다.

## 제출 전 검사

```bash
python task1_sketches.py --verify
python bench.py --yours
python test_regressions.py
python test_tasks.py
python ../check.py w04
```

`out/` 결과물은 전부 저장소에 커밋한다. 관찰 기록은 과제별 3줄이다.
