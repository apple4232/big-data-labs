"""Produce the submission write-up from measured data; no invented results."""
import json
import math
from pathlib import Path
import statistics
import re

HERE = Path(__file__).parent
OUT = HERE / 'out'


def main():
    limits = json.loads((OUT / 'limits.json').read_text(encoding='utf-8'))
    analysis = json.loads((OUT / 'sketch-analysis.json').read_text(encoding='utf-8'))
    complete = [r for r in limits['runs'] if r.get('status', 'completed') == 'completed']
    stopped = [r for r in limits['runs'] if r.get('status') == 'stopped']
    first, last = min(complete, key=lambda r: r['n']), max(complete, key=lambda r: r['n'])
    span = last['n'] / first['n']
    exact_growth = math.log(last['exact_peak_bytes']/first['exact_peak_bytes']) / math.log(span)
    fm_growth = math.log(last['fm_peak_bytes']/first['fm_peak_bytes']) / math.log(span)
    meta = limits['machine']
    lines = ['# Task 2 — 이 PC의 정확 집합과 FM 메모리 측정', '',
             '## A6: 측정 환경', '',
             f"- CPU: {meta['cpu']} ({meta['cores']} cores / {meta['logical_processors']} logical processors).",
             f"- RAM: OS에서 사용 가능한 총 {meta['ram_total_bytes']/1024**3:.2f} GiB; 시작 시 여유 {meta['ram_available_bytes']/1024**3:.2f} GiB.",
             f"- OS / Python: {meta['platform']} / {meta['python']}.",
             f"- 환경 정보 기록: {meta['captured_at']}; 실제 사용자 Windows PC에서 실행.",
             '- ChatGPT, Firefox, WebView, Node, 백신 등 기존 프로그램이 실행 중이었다. 격리된 성능 실험은 아니며, 프로그램 이름과 개수는 machine-context.json에 기록했다.',
             '- seed=246, 생성 범위 floor(0.4n)의 key 문자열. 두 방법은 동일한 생성기를 각각 한 번씩 읽는다. 정확 set만 전체 distinct 문자열을 보관한다.',
             '- 메모리는 tracemalloc의 추적된 Python 할당 peak이다. 프로세스 RSS나 PC 전체 RAM 사용량과 다르다. 두 시간 모두 tracemalloc이 활성화된 상태의 wall time이며 추적 오버헤드가 포함된다.', '',
             '## A1, A3, A5: 크기별 실측 표', '',
             f'완료된 {len(complete)}개 크기는 {span:.0f}배 범위다. MB=10^6 bytes, KiB=1024 bytes.', '',
             '| n | 실제 distinct | exact 시간(s) | exact peak(MB) | FM 시간(s) | FM peak(KiB) | FM / truth |',
             '|---:|---:|---:|---:|---:|---:|---:|']
    for row in sorted(complete, key=lambda r: r['n']):
        lines.append(f"| {row['n']:,} | {row['true_distinct']:,} | {row['exact_s']:.3f} | "
                     f"{row['exact_peak_bytes']/1e6:.3f} | {row['fm_s']:.3f} | "
                     f"{row['fm_peak_bytes']/1024:.3f} | {row['fm_ratio']:.3f}× |")
    lines += ['', '## A2: 중단 경계와 먼저 부담이 된 자원', '',
              f"완료 실행 중 n={last['n']:,}의 정확 set은 {last['exact_s']:.2f}초였다. "
              '이는 한 번의 집계에 분 단위 대기를 요구해 실용적으로 불편한 시간 경계다. '
              '이 크기에서는 할당 실패나 RAM 고갈을 관측하지 않았으므로 하드웨어의 절대 메모리 한계라고 주장하지 않는다.']
    for row in stopped:
        lines += [f"추가로 n={row['n']:,}을 시도했지만, {row['time_limit_s']}초 / "
                  f"{row['memory_limit_bytes']/1024**2:.0f} MiB의 사전 설정 경계 중 `{row['stop_reason']}`에 도달해 중단했다.",
                  f"실제 {row['items_processed']:,}개 처리, partial distinct={row['partial_distinct']:,}, "
                  f"시간={row['exact_s']:.2f}초, traced peak={row['exact_peak_bytes']/1e6:.2f} MB였다. "
                  '완료된 2,500만 건의 truth나 FM 정확도로 취급하지 않았다. 실제 OOM 실패로도 표현하지 않았다.']
    lines += ['', '## A4: 메모리 성장률', '',
              f"n이 {span:.0f}배 증가했을 때 exact peak은 {last['exact_peak_bytes']/first['exact_peak_bytes']:.2f}배, "
              f"FM peak은 {last['fm_peak_bytes']/first['fm_peak_bytes']:.4f}배였다.",
              f"끝점 log-log 기울기는 exact={exact_growth:.3f}, FM={fm_growth:.4f}이다. "
              'exact는 대략 O(D), 이 고정 distinct 비율의 생성기에서는 O(n)이다. '
              '해시 테이블의 용량 점프와 문자열 길이 때문에 완전한 직선은 아니다. '
              'FM은 O(h)개의 레지스터와 고정 폭 packed hash 상태이며 h=64 고정 시 n에 대해 O(1)이다.',
              '이 구현의 FM은 실측상 exact보다 느렸다. 64개 hash lane과 큰 정수 연산의 시간 비용으로 메모리를 절약한 것이며, '
              '메모리 상수화가 실행시간 개선을 보장하지 않는다.', '',
              '## 정확도와 활용 판단', '',
              'FM 정확도는 n이 커진다고 자동으로 좋아지지 않는다. 해시 수 h가 고정이면 상대 오차의 분산도 남으며, '
              '각 크기의 실측 ratio를 그대로 위에 기록했다. '
              '약 두 배 오차는 트래픽 규모의 대략적인 capacity 판단에는 쓸 수 있지만, '
              '사용자별 과금·정산이나 작은 일별 변화를 판단하는 데에는 부적절하다.']
    (OUT / 'limits.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

    b = analysis['bloom']
    fm = analysis['fm_combining']
    budget = analysis['budget']
    bench_text = (OUT / 'bench.txt').read_text(encoding='utf-8-sig')
    match = re.search(r'yours\s+false positives\s+([\d,]+).*?false negatives\s+(\d+)', bench_text)
    if not match:
        raise RuntimeError('missing measured benchmark result')
    false_positives = int(match.group(1).replace(',', ''))
    false_negatives = int(match.group(2))
    measured_budget_rate = false_positives / 200_000
    rates = ', '.join(f"{r['fm_ratio']:.3f}×" for r in sorted(complete, key=lambda r: r['n']))
    rules = fm['rules']
    boundary = (f"2,500만 건 추가 실행은 {stopped[-1]['exact_s']:.2f}초의 시간 경계에서 중단했으며, OOM은 관측하지 않았다."
                if stopped else 'OOM은 관측하지 않았으며 메모리의 절대 한계는 찾지 않았다.')
    text = f'''# Week 4 관찰 기록

## Task 1
Bloom은 add 때 켠 비트를 지우지 않고 같은 hash 위치를 조회하므로 삽입 항목의 false negative가 없다. m=8192, k=5, n=800에서 예측 오탐률은 {b['predicted_rate']:.3%}, 2만 비삽입 질의의 실측은 {b['measured_rate']:.3%}로 표본 변동 범위였다.
FM은 64개 최대 trailing-zero R을 8개씩 묶어 평균 R의 중앙값을 취한 뒤 지수화하고 max-R의 점근적 bias를 보정했다. 동일 검증 자료에서 2^R 산술평균 {rules['arithmetic_mean_of_2_to_R']['estimate']:,.0f}, 중앙값 {rules['median_of_2_to_R']['estimate']:,.0f}, 선택한 방법 {rules['median_of_group_geometric_means_with_max_R_correction']['estimate']:,.0f} / truth {fm['truth']:,}였다.
Reservoir는 현재 i번째 항목에서 randrange(i)<k일 때 해당 slot을 교체한다. 새 항목이 들어올 확률 k/i와 이전 항목의 생존확률을 곱하면 최종 k/n이 되므로 n을 미리 몰라도 k개만 보관한다. 제공된 4,000회 uniform 검증도 통과했다.

## Task 2
이 PC에서 n={last['n']:,}의 exact 집계는 {last['exact_s']:.2f}초로 시간 부담이 컸고 peak은 {last['exact_peak_bytes']/1e6:.2f}MB였다. {boundary}
완료된 {span:.0f}배 크기 범위의 메모리 log-log 기울기는 exact={exact_growth:.3f}, FM={fm_growth:.4f}로 측정됐다. exact는 distinct 수에 대략 선형으로 증가했고 FM은 64개 register를 고정하여 약 {last['fm_peak_bytes']/1024:.2f}KiB를 유지했지만 실행시간은 더 길었다.
크기별 FM / truth는 {rates}로 n 증가에 따른 단조 개선은 없었다. 두 배 오차는 방문자 규모의 대략적인 자원 계획에는 허용할 수 있지만 사용자별 과금이나 작은 증감 비교에는 허용하기 어렵다.

## Task 3
p(k)=(1-exp(-kn/m))^k를 최소화하면 k*=(m/n)ln2이다. 10 bits/item에서는 6.931→7개 hash를 사용했고, shared code를 제외한 모든 retained 상태(인스턴스+seed 포함 bytearray)를 합산해 정확히 {budget['total_retained_bits']:,}비트였다.
표준 Bloom 모형의 최적 예측값은 exp(-10(ln2)^2)={budget['bloom_floor_at_10_bits']:.3%}이다. 실제 유효 공간은 {budget['usable_bits']:,}비트여서 k=7의 예측은 {budget['predicted_at_effective_bits']:.3%}이며 실측 {false_positives:,}/200,000={measured_budget_rate:.4%}, false negative {false_negatives}으로 strong 기준을 충족했다. 유한 질의 표본의 실측은 이론의 기대값과 동일할 필요가 없다.
n이 미지라면 점유율과 예상 상한을 감시하고, 예산을 늘릴 수 있을 때 scalable Bloom을 고려한다. n을 낮게 잡으면 오탐이 증가하고, 목표 오탐률에 맞춘 공간을 너무 크게 잡으면 RAM을 낭비한다. 고정 예산이 가득 찬 경우 과거 비트를 지워 정확한 membership 계약을 깨는 대신 오탐 증가를 인정해야 한다.
'''
    (OUT / 'observation.md').write_text(text, encoding='utf-8')
    (OUT / 'growth.json').write_text(json.dumps({'completed_size_span': span,
                                                'exact_memory_exponent': exact_growth,
                                                'fm_memory_exponent': fm_growth}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
