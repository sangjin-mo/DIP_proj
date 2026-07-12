# Arduino 8x8 LED 한글시계

## 1. 수행 목표

Arduino UNO, MAX7219 8x8 LED 매트릭스, DS1307 RTC를 이용해 현재 시간을 한글 워드클럭 방식으로 표시하는 구조를 정리한다.

핵심 목표는 다음과 같다.

- RTC에서 현재 시각 읽기
- 숫자 시간을 한글 표현으로 변환
- 8x8 LED 매트릭스의 특정 좌표 점등
- 오전/오후, 정각, 1분 단위 표시
- USB Serial을 이용한 RTC 시간 동기화
- Wokwi 시뮬레이션과 실제 하드웨어 제약사항 정리

---

## 2. 실습 구성

| 구분 | 내용 |
| --- | --- |
| 제어 보드 | Arduino UNO |
| 표시 장치 | MAX7219 8x8 LED Dot Matrix |
| 시간 장치 | DS1307 RTC |
| 개발환경 | Wokwi |
| LED 라이브러리 | LedControl |
| RTC 라이브러리 | RTClib |
| RTC 통신 | I2C |
| LED 통신 | DIN, CLK, CS |

실제 제작 시에는 LED 위에 올릴 한글 문자판, 확산판, 격벽, 케이스, DS1307 코인전지가 추가로 필요하다.

---

## 3. 시스템 흐름

```text
DS1307 RTC
→ Arduino UNO
→ 시간 분석 및 한글 좌표 변환
→ MAX7219
→ 8x8 LED Matrix
→ 한글 문자판 표시
```

Arduino는 RTC에서 현재 시와 분을 읽고, 해당 시간에 필요한 한글 위치의 LED만 켠다.

---

## 4. 회로 연결

### 4.1 MAX7219 LED Matrix

| Arduino UNO | MAX7219 | 기능 |
| --- | --- | --- |
| 5V | VCC | 전원 |
| GND | GND | 접지 |
| D11 | DIN | 데이터 |
| D13 | CLK | 클럭 |
| D10 | CS | 장치 선택 |

### 4.2 DS1307 RTC

| Arduino UNO | DS1307 | 기능 |
| --- | --- | --- |
| 5V | VCC | 전원 |
| GND | GND | 접지 |
| A4 | SDA | I2C 데이터 |
| A5 | SCL | I2C 클럭 |

모든 부품의 GND는 공통으로 연결해야 한다.

---

## 5. 8x8 한글 문자판

LED 하나가 한글 한 글자를 담당하는 워드클럭 방식으로 구성한다.

```text
      X →  0  1  2  3  4  5  6  7

Y=0       열 한 두 세 네 다 여 섯
Y=1       일 곱 덟 아 홉 시 정 각
Y=2       이 삼 사 오 십 일 이 삼
Y=3       사 오 육 칠 팔 구 분 ·
Y=4       오 전 오 후 ·  ·  ·  ·
Y=5       ·  ·  ·  ·  ·  ·  ·  ·
Y=6       ·  ·  ·  ·  ·  ·  ·  ·
Y=7       ·  ·  ·  ·  ·  ·  ·  ·
```

예를 들어 `03:25`는 다음 글자를 켠다.

```text
오 + 전 + 세 + 시 + 이 + 십 + 오 + 분
```

표시 문장은 `오전 세시 이십오분`이 된다.

---

## 6. 시간 변환 알고리즘

### 6.1 12시간 변환

```cpp
hour12 = hour24 % 12;

if (hour12 == 0) {
  hour12 = 12;
}
```

| RTC 시각 | 표시 |
| ---: | --- |
| 00시 | 오전 열두시 |
| 03시 | 오전 세시 |
| 12시 | 오후 열두시 |
| 15시 | 오후 세시 |
| 23시 | 오후 열한시 |

### 6.2 분 표시

분은 십의 자리와 일의 자리로 나누어 표시한다.

```cpp
int tens = minute / 10;
int ones = minute % 10;
```

예시는 다음과 같다.

| 분 | 표시 |
| ---: | --- |
| 0 | 정각 |
| 1 | 일분 |
| 10 | 십분 |
| 25 | 이십오분 |
| 48 | 사십팔분 |
| 59 | 오십구분 |

---

## 7. 핵심 코드 구조

전체 코드는 RTC 읽기, LED 좌표 점등, 시간 표시 함수로 나누어 구성한다.

```cpp
#include <Wire.h>
#include <RTClib.h>
#include <LedControl.h>

const byte DIN_PIN = 11;
const byte CLK_PIN = 13;
const byte CS_PIN  = 10;

LedControl matrix(DIN_PIN, CLK_PIN, CS_PIN, 1);
RTC_DS1307 rtc;

int lastHour = -1;
int lastMinute = -1;

void turnOn(byte x, byte y) {
  if (x >= 8 || y >= 8) {
    return;
  }

  matrix.setLed(0, y, x, true);
}

void clearMatrix() {
  matrix.clearDisplay(0);
}

void displayPeriod(byte hour24) {
  if (hour24 < 12) {
    turnOn(0, 4);  // 오
    turnOn(1, 4);  // 전
  } else {
    turnOn(2, 4);  // 오
    turnOn(3, 4);  // 후
  }
}

void displayHour(byte hour24) {
  byte hour12 = hour24 % 12;

  if (hour12 == 0) {
    hour12 = 12;
  }

  switch (hour12) {
    case 1:
      turnOn(1, 0);  // 한
      break;
    case 2:
      turnOn(2, 0);  // 두
      break;
    case 3:
      turnOn(3, 0);  // 세
      break;
    case 10:
      turnOn(0, 0);  // 열
      break;
    case 11:
      turnOn(0, 0);  // 열
      turnOn(1, 0);  // 한
      break;
    case 12:
      turnOn(0, 0);  // 열
      turnOn(2, 0);  // 두
      break;
  }

  turnOn(5, 1);      // 시
}

void displayMinute(byte minute) {
  if (minute == 0) {
    turnOn(6, 1);  // 정
    turnOn(7, 1);  // 각
    return;
  }

  byte tens = minute / 10;
  byte ones = minute % 10;

  // 실제 코드에서는 tens와 ones에 따라 좌표를 점등한다.
  // 예: 25분 → 이 + 십 + 오 + 분

  turnOn(6, 3);      // 분
}

void displayTime(byte hour, byte minute) {
  clearMatrix();
  displayPeriod(hour);
  displayHour(hour);
  displayMinute(minute);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  matrix.shutdown(0, false);
  matrix.setIntensity(0, 5);
  matrix.clearDisplay(0);

  if (!rtc.begin()) {
    Serial.println("RTC connection failed.");
    while (true) {
      delay(100);
    }
  }
}

void loop() {
  DateTime now = rtc.now();

  if (now.hour() != lastHour || now.minute() != lastMinute) {
    lastHour = now.hour();
    lastMinute = now.minute();

    displayTime(now.hour(), now.minute());
  }

  delay(200);
}
```

위 코드는 핵심 구조만 남긴 축약 예시이다.
실제 완성 코드에서는 1~12시와 0~59분의 모든 좌표 변환을 `switch`문으로 추가해야 한다.

---

## 8. PC 시간 동기화

Arduino UNO에는 네트워크 기능이 없으므로 USB Serial 명령으로 RTC 시간을 맞춘다.

```text
T 2026 7 11 15 30 0
```

의미는 다음과 같다.

```text
2026년 7월 11일 15시 30분 0초
```

프로그램에서는 명령을 읽어 `rtc.adjust()`로 RTC 시간을 수정한다.

---

## 9. 예상 표시 결과

| RTC 시간 | 점등 글자 | 표시 |
| --- | --- | --- |
| 03:25 | 오 전 세 시 이 십 오 분 | 오전 세시 이십오분 |
| 08:48 | 오 전 여 덟 시 사 십 팔 분 | 오전 여덟시 사십팔분 |
| 12:00 | 오 후 열 두 시 정 각 | 오후 열두시 정각 |
| 23:59 | 오 후 열 한 시 오 십 구 분 | 오후 열한시 오십구분 |

---

## 10. 제약사항

| 제약 | 설명 |
| --- | --- |
| 8x8 해상도 | 한글 글꼴을 직접 그리기 어렵다. |
| 문자판 필요 | LED 위에 한글 글자가 적힌 전면판이 필요하다. |
| 문자 중복 | 시간과 분에서 같은 글자가 필요해 좌표 배치가 중요하다. |
| 방향 차이 | 매트릭스 모듈에 따라 좌우, 상하가 뒤집힐 수 있다. |
| RTC 오차 | DS1307은 장시간 사용 시 오차가 누적될 수 있다. |
| Wokwi 한계 | 실제 문자판, 빛 번짐, 코인전지 유지는 검증하기 어렵다. |

---

## 11. 메모리 절약

Arduino UNO의 SRAM은 작으므로 다음 방식을 사용한다.

- 한글 폰트 비트맵을 저장하지 않는다.
- 문자열을 조합하지 않는다.
- 필요한 LED 좌표만 직접 점등한다.
- 큰 배열과 동적 메모리 할당을 피한다.
- 시 또는 분이 바뀔 때만 화면을 갱신한다.

---

## 12. 최종 확인

| 확인 항목 | 상태 |
| --- | --- |
| MAX7219 연결 설명 | 완료 |
| DS1307 연결 설명 | 완료 |
| 8x8 한글 문자판 설계 | 완료 |
| 12시간 변환 알고리즘 | 완료 |
| 1분 단위 표시 방식 | 완료 |
| 오전/오후 표시 | 완료 |
| 정각 표시 | 완료 |
| PC 시간 동기화 방식 | 완료 |
| 실제 문자판 제작 | 미수행 |
| 실제 코인전지 시험 | 미수행 |

---

## 13. 정리

이 프로젝트는 Arduino UNO가 DS1307 RTC에서 현재 시각을 읽고, MAX7219 8x8 LED 매트릭스의 특정 좌표를 켜서 시간을 한글로 표현하는 워드클럭이다.

8x8 해상도에서는 한글 글꼴을 직접 표시하기 어렵기 때문에 LED 하나가 한글 문자판의 한 글자를 담당하는 방식이 적합하다.
Wokwi에서는 회로와 기본 알고리즘을 확인할 수 있지만, 실제 문자판의 밝기, 빛 확산, 코인전지 유지, 케이스 구조는 실제 제작 단계에서 추가 검증해야 한다.
