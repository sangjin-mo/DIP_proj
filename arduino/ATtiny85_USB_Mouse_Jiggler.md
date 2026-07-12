# ATtiny85 USB Mouse Jiggler

## 1. 수행 목표

ATtiny85와 USB HID 통신을 이용해 마우스 상대 이동을 발생시키는 Mouse Jiggler의 원리와 코드 구조를 정리한다.

핵심 목표는 다음과 같다.

1. ATtiny85와 V-USB의 기본 원리 이해
2. USB HID 마우스 동작 방식 이해
3. 무작위 대기, 방향, 거리 생성 알고리즘 작성
4. 이동 후 반대 방향으로 복귀하는 구조 설계
5. ATtiny85의 메모리와 성능 제약 고려

> 본 문서는 USB HID 학습과 개인 장비 시험을 위한 것이다. 조직의 화면 잠금, 보안 또는 근태 정책을 우회하는 목적으로 사용해서는 안 된다.

---

## 2. 실습 범위

현재 ATtiny85 또는 Digispark 하드웨어가 없으므로 실제 USB 연결과 포인터 이동은 검증하지 않는다.
따라서 본 문서는 원리, 알고리즘, 참고 코드, 예상 동작을 중심으로 작성한다.

| 항목 | 내용 |
| --- | --- |
| MCU | ATtiny85 |
| USB 방식 | V-USB 소프트웨어 USB |
| 장치 형태 | USB HID 마우스 |
| 라이브러리 | DigiMouse |
| 실제 검증 | 하드웨어 부재로 미수행 |

---

## 3. ATtiny85 특징

ATtiny85는 소형 임베디드 장치에 사용되는 8-bit AVR 마이크로컨트롤러이다.

| 항목 | 사양 |
| --- | ---: |
| CPU | 8-bit AVR |
| Flash | 8KB |
| SRAM | 512B |
| EEPROM | 512B |
| I/O | 최대 6개 |
| ADC | 10-bit |

메모리가 작기 때문에 큰 배열, 긴 문자열, 동적 메모리 할당은 피하는 것이 좋다.

---

## 4. USB HID와 DigiMouse

ATtiny85에는 네이티브 USB 주변장치가 없기 때문에 Digispark 계열은 V-USB로 USB Low-Speed 장치를 소프트웨어 구현한다.

```text
PC USB Host
↔ USB D+ / D-
↔ V-USB
↔ ATtiny85 프로그램
```

USB HID 마우스는 버튼 상태, X/Y 상대 이동량, 스크롤 값을 컴퓨터에 보고한다.

```text
버튼 = 0
X 이동 = +2
Y 이동 = 0
스크롤 = 0
```

DigiMouse의 주요 함수는 다음과 같다.

| 함수 | 역할 |
| --- | --- |
| `DigiMouse.begin()` | USB 마우스 시작 |
| `DigiMouse.move(x, y, wheel)` | X/Y/스크롤 상대 이동 |
| `DigiMouse.delay(ms)` | USB 통신을 유지하면서 대기 |
| `DigiMouse.update()` | USB 상태 갱신 |

V-USB는 소프트웨어로 USB를 처리하므로 긴 대기 중에도 `DigiMouse.delay()` 또는 `update()`가 필요하다.

---

## 5. 구현 조건

| 조건 | 구현 |
| --- | --- |
| 대기 시간 | 1~59초 무작위 |
| 이동 거리 | 1~3 무작위 |
| 이동 방향 | 상, 하, 좌, 우 중 무작위 |
| 위치 복귀 | `(dx, dy)` 이동 후 `(-dx, -dy)` 이동 |
| 반복 | `loop()`에서 무한 반복 |
| 클릭 방지 | 버튼과 스크롤은 사용하지 않음 |

---

## 6. 알고리즘

```text
USB HID 마우스 초기화
→ 1~59초 무작위 대기
→ 1~3 이동 거리 선택
→ 상/하/좌/우 방향 선택
→ (dx, dy) 이동
→ 짧게 대기
→ (-dx, -dy) 이동
→ 반복
```

방향별 이동값은 다음과 같다.

| 방향 | dx | dy |
| --- | ---: | ---: |
| 오른쪽 | +distance | 0 |
| 왼쪽 | -distance | 0 |
| 아래 | 0 | +distance |
| 위 | 0 | -distance |

이동 후 반대 방향으로 같은 크기만큼 이동하면 코드상 상대 이동량의 합은 0이 된다.

```text
(dx, dy) + (-dx, -dy) = (0, 0)
```

---

## 7. 참고 코드

아래 코드는 Digispark ATtiny85와 DigiMouse 라이브러리를 가정한 참고 코드이다.
현재 환경에서는 실제 컴파일과 USB HID 동작을 검증하지 않았다.

```cpp
#include <DigiMouse.h>
#include <stdint.h>

const long MIN_WAIT_SEC = 1;
const long MAX_WAIT_SEC = 59;

const int MIN_DISTANCE = 1;
const int MAX_DISTANCE = 3;

void createRandomMove(int8_t &dx, int8_t &dy) {
  int8_t distance = (int8_t)random(MIN_DISTANCE, MAX_DISTANCE + 1);
  int direction = random(0, 4);

  dx = 0;
  dy = 0;

  switch (direction) {
    case 0:
      dx = distance;
      break;
    case 1:
      dx = -distance;
      break;
    case 2:
      dy = distance;
      break;
    case 3:
      dy = -distance;
      break;
  }
}

void setup() {
  DigiMouse.begin();
  randomSeed(analogRead(1) ^ micros());
  DigiMouse.delay(1000);
}

void loop() {
  long waitSeconds = random(MIN_WAIT_SEC, MAX_WAIT_SEC + 1);
  DigiMouse.delay(waitSeconds * 1000L);

  int8_t dx;
  int8_t dy;

  createRandomMove(dx, dy);

  DigiMouse.move((char)dx, (char)dy, 0);
  DigiMouse.delay(random(40L, 151L));

  DigiMouse.move((char)-dx, (char)-dy, 0);
  DigiMouse.delay(random(30L, 101L));
}
```

---

## 8. 예상 동작

예상 동작 예시는 다음과 같다.

```text
대기 시간: 17초
이동 거리: 2
방향: 오른쪽

첫 이동: (+2, 0)
복귀 이동: (-2, 0)
최종 합계: (0, 0)
```

전체 흐름은 다음과 같다.

```text
USB 장치 연결
→ HID 마우스로 인식
→ 무작위 시간 대기
→ 포인터 1~3만큼 이동
→ 반대 방향으로 복귀
→ 반복
```

---

## 9. 제약사항

| 제약 | 설명 |
| --- | --- |
| 실제 좌표 복귀 | 화면 가장자리, 마우스 가속, 다중 모니터 환경에서는 정확히 보장되지 않을 수 있음 |
| USB 유지 | 일반 `delay()`보다 `DigiMouse.delay()` 사용이 적합 |
| 난수 | `random()`은 의사 난수이므로 완전한 무작위는 아님 |
| 호환성 | Digispark 보드 패키지, 드라이버, Arduino IDE 버전에 영향받음 |
| 메모리 | 8KB Flash, 512B SRAM 안에서 단순하게 작성해야 함 |

---

## 10. 하드웨어 없이 확인 가능한 내용

| 확인 항목 | 가능 여부 |
| --- | --- |
| 대기 시간 범위 | 코드 분석으로 가능 |
| 이동 거리 1~3 | 코드 분석으로 가능 |
| 방향 무작위 선택 | 코드 분석으로 가능 |
| 반대 이동 계산 | 수식으로 가능 |
| 무한 반복 구조 | `loop()` 구조로 가능 |
| 실제 USB 인식 | 하드웨어 필요 |
| 실제 포인터 이동 | 하드웨어 필요 |

---

## 11. 최종 확인

| 항목 | 상태 |
| --- | --- |
| ATtiny85 특징 설명 | 완료 |
| V-USB 원리 설명 | 완료 |
| USB HID 마우스 원리 설명 | 완료 |
| 1~59초 대기 설정 | 완료 |
| 1~3 이동 거리 설정 | 완료 |
| 반대 방향 복귀 설계 | 완료 |
| 실제 보드 검증 | 미수행 |

---

## 12. 정리

ATtiny85는 자원이 제한된 8-bit MCU이며, Digispark 계열에서는 V-USB를 사용해 USB HID 장치처럼 동작할 수 있다.
DigiMouse 라이브러리를 사용하면 X/Y 상대 이동량을 컴퓨터에 전달하여 마우스 이동을 구현할 수 있다.

본 프로그램은 무작위 대기 후 작은 거리로 포인터를 이동하고, 곧바로 반대 방향으로 이동하여 코드상 최종 상대 이동량이 0이 되도록 설계하였다.
실제 USB 인식과 포인터 동작은 ATtiny85 또는 Digispark 하드웨어 확보 후 검증해야 한다.
