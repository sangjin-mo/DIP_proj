# 아두이노 센서 기반 LED 제어

## 1. 수행 목표

본 문서는 아두이노에 온도 센서, 조도 센서, 거리 센서를 연결하고, 각 센서 데이터를 읽어 LED 밝기와 색상을 제어하는 방법을 정리하기 위해 작성하였다.

주요 목표는 다음과 같다.

1. 아두이노에 온도, 조도, 거리 센서를 연결하는 방법을 설명한다.
2. 각 센서로부터 데이터를 읽어오는 아두이노 코드를 작성한다.
3. 센서 데이터에 따라 LED 밝기와 색상을 조절하는 알고리즘을 설계한다.
4. 조건에 따라 LED를 다르게 제어하는 통합 프로그램을 구현한다.
5. 센서 데이터 처리와 LED 제어 로직을 통합하는 방법을 설명한다.
6. 센서에서 발생하는 에러를 걸러내는 방법을 설명한다.

---

## 2. 개발환경

| 구분    | 내용                      |
| ----- | ----------------------- |
| 개발 보드 | Arduino UNO 기준          |
| 개발 도구 | Arduino IDE             |
| 운영체제  | Windows 또는 Linux        |
| 사용 센서 | 온도 센서, 조도 센서, 초음파 거리 센서 |
| 출력 장치 | RGB LED 또는 NeoPixel LED |
| 사용 언어 | Arduino C/C++           |

본 문서에서는 다음 부품을 기준으로 설명한다.

| 부품    | 예시                          |
| ----- | --------------------------- |
| 온도 센서 | LM35 또는 TMP36 계열 아날로그 온도 센서 |
| 조도 센서 | CDS 조도 센서                   |
| 거리 센서 | HC-SR04 초음파 거리 센서           |
| LED   | RGB LED 또는 NeoPixel LED     |
| 기타 부품 | 저항, 브레드보드, 점퍼 케이블           |

---

## 3. 전체 시스템 구조

센서 기반 LED 제어 시스템은 다음과 같은 흐름으로 동작한다.

```text
[온도 센서] ─┐
[조도 센서] ─┼→ [Arduino UNO] → [LED 밝기/색상 제어]
[거리 센서] ─┘
```

아두이노는 각 센서에서 값을 읽고, 센서값을 조건에 따라 판단한 뒤 LED의 밝기 또는 색상을 변경한다.

---

## 4. 센서 연결 방법

## 4.1 온도 센서 연결

온도 센서는 주변 온도를 전압 값으로 변환하여 아두이노에 전달한다.
아날로그 온도 센서를 사용하는 경우 아두이노의 아날로그 입력 핀에 연결한다.

| 온도 센서 핀 | 아두이노 연결 |
| ------- | ------- |
| VCC     | 5V      |
| GND     | GND     |
| OUT     | A0      |

연결 구조는 다음과 같다.

```text
[온도 센서]
 VCC ─→ 5V
 GND ─→ GND
 OUT ─→ A0
```

아두이노는 A0 핀에서 아날로그 값을 읽고, 이를 전압과 온도로 변환한다.

---

## 4.2 조도 센서 연결

조도 센서는 빛의 세기에 따라 저항값이 변하는 센서이다.
일반적으로 저항과 함께 전압 분배 회로를 구성하여 아날로그 값을 읽는다.

| 구성 요소     | 아두이노 연결 |
| --------- | ------- |
| 조도 센서 한쪽  | 5V      |
| 조도 센서 다른쪽 | A1      |
| 고정 저항 한쪽  | A1      |
| 고정 저항 다른쪽 | GND     |

연결 구조는 다음과 같다.

```text
5V ─→ [조도 센서] ─→ A1 ─→ [10kΩ 저항] ─→ GND
```

빛이 밝아지거나 어두워지면 A1에서 읽히는 아날로그 값이 변한다.

---

## 4.3 거리 센서 연결

HC-SR04 초음파 거리 센서는 초음파를 보내고 다시 돌아오는 시간을 측정하여 거리를 계산한다.

| HC-SR04 핀 | 아두이노 연결 |
| --------- | ------- |
| VCC       | 5V      |
| GND       | GND     |
| TRIG      | D8      |
| ECHO      | D9      |

연결 구조는 다음과 같다.

```text
[HC-SR04]
 VCC  ─→ 5V
 GND  ─→ GND
 TRIG ─→ D8
 ECHO ─→ D9
```

TRIG 핀으로 초음파 발생 신호를 보내고, ECHO 핀에서 돌아오는 신호 시간을 측정한다.

---

## 4.4 RGB LED 연결

RGB LED는 빨강, 초록, 파랑 LED가 하나로 합쳐진 LED이다.
각 색상 핀에 PWM 신호를 주면 색상을 조합할 수 있다.

| RGB LED 핀 | 아두이노 연결 |
| --------- | ------- |
| R         | D3      |
| G         | D5      |
| B         | D6      |
| 공통 GND    | GND     |

각 색상 핀에는 전류 제한을 위해 220Ω 정도의 저항을 연결하는 것이 좋다.

```text
D3 ─→ 저항 ─→ R
D5 ─→ 저항 ─→ G
D6 ─→ 저항 ─→ B
GND ─→ 공통 GND
```

---

## 5. 센서 데이터 읽기 코드

## 5.1 온도 센서 데이터 읽기

아날로그 온도 센서는 아두이노의 ADC 값을 통해 읽을 수 있다.

```cpp
int tempPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int rawValue = analogRead(tempPin);

  float voltage = rawValue * (5.0 / 1023.0);
  float temperatureC = voltage * 100.0;  // LM35 기준: 10mV = 1도

  Serial.print("Temperature: ");
  Serial.print(temperatureC);
  Serial.println(" C");

  delay(500);
}
```

---

## 5.2 조도 센서 데이터 읽기

조도 센서는 아날로그 값으로 읽는다.
값의 범위는 일반적으로 0~1023이다.

```cpp
int lightPin = A1;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int lightValue = analogRead(lightPin);

  Serial.print("Light: ");
  Serial.println(lightValue);

  delay(500);
}
```

---

## 5.3 거리 센서 데이터 읽기

초음파 거리 센서는 TRIG 핀으로 신호를 보내고, ECHO 핀에서 신호가 돌아오는 시간을 측정한다.

```cpp
int trigPin = 8;
int echoPin = 9;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  long duration;
  float distanceCm;

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distanceCm = duration * 0.034 / 2.0;

  Serial.print("Distance: ");
  Serial.print(distanceCm);
  Serial.println(" cm");

  delay(500);
}
```

---

## 6. LED 제어 알고리즘 설계

센서 데이터를 이용해 LED를 다음과 같이 제어한다.

| 센서    | 조건        | LED 동작            |
| ----- | --------- | ----------------- |
| 조도 센서 | 주변이 어두움   | LED 밝기 증가         |
| 조도 센서 | 주변이 밝음    | LED 밝기 감소         |
| 온도 센서 | 온도가 높음    | LED를 빨간색으로 표시     |
| 온도 센서 | 온도가 보통    | LED를 초록색으로 표시     |
| 온도 센서 | 온도가 낮음    | LED를 파란색으로 표시     |
| 거리 센서 | 물체가 가까움   | LED를 빠르게 점멸       |
| 거리 센서 | 물체가 멀리 있음 | LED를 천천히 점멸 또는 유지 |

---

## 7. LED 제어 로직

### 7.1 온도에 따른 색상 제어

| 온도 범위         | LED 색상 |
| ------------- | ------ |
| 20℃ 미만        | 파란색    |
| 20℃ 이상 30℃ 미만 | 초록색    |
| 30℃ 이상        | 빨간색    |

### 7.2 조도에 따른 밝기 제어

| 조도 값    | 주변 상태 | LED 밝기 |
| ------- | ----- | ------ |
| 700 이상  | 밝음    | 약하게    |
| 300~700 | 보통    | 중간     |
| 300 미만  | 어두움   | 밝게     |

### 7.3 거리에 따른 점멸 제어

| 거리              | 상태     | LED 동작 |
| --------------- | ------ | ------ |
| 10cm 미만         | 매우 가까움 | 빠르게 점멸 |
| 10cm 이상 30cm 미만 | 가까움    | 천천히 점멸 |
| 30cm 이상         | 멀리 있음  | 점등 유지  |

---

## 8. 통합 프로그램 구현

아래 코드는 온도 센서, 조도 센서, 거리 센서 데이터를 읽고, 조건에 따라 RGB LED의 색상과 밝기를 제어하는 통합 프로그램이다.

```cpp
// 아두이노 센서 기반 RGB LED 제어 프로그램

// 센서 핀 설정
const int tempPin = A0;
const int lightPin = A1;
const int trigPin = 8;
const int echoPin = 9;

// RGB LED 핀 설정
const int redPin = 3;
const int greenPin = 5;
const int bluePin = 6;

// 센서값 저장 변수
float temperatureC = 0.0;
int lightValue = 0;
float distanceCm = 0.0;

void setup() {
  Serial.begin(9600);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
}

void loop() {
  // 1. 센서 데이터 읽기
  temperatureC = readTemperature();
  lightValue = readLight();
  distanceCm = readDistance();

  // 2. 센서 에러 확인
  if (isSensorError(temperatureC, lightValue, distanceCm)) {
    setColor(255, 0, 255);  // 에러 발생 시 보라색 표시
    Serial.println("Sensor Error Detected");
    delay(500);
    return;
  }

  // 3. LED 제어
  controlLed(temperatureC, lightValue, distanceCm);

  // 4. 시리얼 모니터 출력
  Serial.print("Temp: ");
  Serial.print(temperatureC);
  Serial.print(" C, Light: ");
  Serial.print(lightValue);
  Serial.print(", Distance: ");
  Serial.print(distanceCm);
  Serial.println(" cm");

  delay(300);
}

// 온도 읽기 함수
float readTemperature() {
  int rawValue = analogRead(tempPin);
  float voltage = rawValue * (5.0 / 1023.0);
  float tempC = voltage * 100.0;  // LM35 기준
  return tempC;
}

// 조도 읽기 함수
int readLight() {
  int value = analogRead(lightPin);
  return value;
}

// 거리 읽기 함수
float readDistance() {
  long duration;
  float distance;

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 30000);  // 30ms timeout

  if (duration == 0) {
    return -1;  // 측정 실패
  }

  distance = duration * 0.034 / 2.0;
  return distance;
}

// LED 제어 함수
void controlLed(float temp, int light, float distance) {
  int brightness;

  // 조도에 따른 밝기 설정
  if (light < 300) {
    brightness = 255;  // 어두우면 밝게
  } else if (light < 700) {
    brightness = 150;  // 보통 밝기
  } else {
    brightness = 50;   // 밝으면 약하게
  }

  // 온도에 따른 기본 색상 설정
  int r = 0;
  int g = 0;
  int b = 0;

  if (temp >= 30) {
    r = brightness;
    g = 0;
    b = 0;
  } else if (temp >= 20) {
    r = 0;
    g = brightness;
    b = 0;
  } else {
    r = 0;
    g = 0;
    b = brightness;
  }

  // 거리 조건에 따른 점멸 제어
  if (distance > 0 && distance < 10) {
    setColor(r, g, b);
    delay(100);
    setColor(0, 0, 0);
    delay(100);
  } else if (distance >= 10 && distance < 30) {
    setColor(r, g, b);
    delay(300);
    setColor(0, 0, 0);
    delay(300);
  } else {
    setColor(r, g, b);
  }
}

// RGB LED 색상 설정 함수
void setColor(int red, int green, int blue) {
  analogWrite(redPin, red);
  analogWrite(greenPin, green);
  analogWrite(bluePin, blue);
}

// 센서 에러 판별 함수
bool isSensorError(float temp, int light, float distance) {
  if (temp < -10 || temp > 80) {
    return true;
  }

  if (light < 0 || light > 1023) {
    return true;
  }

  if (distance == -1 || distance > 400) {
    return true;
  }

  return false;
}
```

---

## 9. 통합 로직 설명

통합 프로그램은 다음 순서로 동작한다.

```text
센서 데이터 읽기
→ 센서값이 정상 범위인지 확인
→ 조도값으로 LED 밝기 결정
→ 온도값으로 LED 색상 결정
→ 거리값으로 점멸 속도 결정
→ RGB LED 출력
→ 시리얼 모니터에 데이터 출력
```

### 9.1 센서 데이터 읽기

`readTemperature()`, `readLight()`, `readDistance()` 함수는 각각 온도, 조도, 거리 센서값을 읽는다.
센서별로 입력 방식이 다르기 때문에 별도의 함수로 분리하였다.

| 함수                | 역할                        |
| ----------------- | ------------------------- |
| readTemperature() | 아날로그 온도 센서값을 읽고 섭씨 온도로 변환 |
| readLight()       | 조도 센서의 아날로그 값을 읽음         |
| readDistance()    | 초음파 센서의 거리값을 cm 단위로 계산    |

### 9.2 센서 에러 확인

`isSensorError()` 함수는 센서값이 정상 범위를 벗어났는지 확인한다.
온도, 조도, 거리값이 비정상적이면 LED를 보라색으로 켜서 에러 상태를 표시한다.

### 9.3 LED 제어

`controlLed()` 함수는 센서값에 따라 LED의 밝기, 색상, 점멸 속도를 결정한다.

* 조도 센서값이 낮으면 주변이 어두운 상태이므로 LED 밝기를 높인다.
* 온도값이 높으면 빨간색, 보통이면 초록색, 낮으면 파란색으로 표시한다.
* 거리값이 가까우면 LED를 빠르게 점멸하여 경고 상태를 표현한다.

---

## 10. 센서 에러를 걸러내는 방법

센서 데이터에는 노이즈나 오류가 포함될 수 있다.
따라서 센서값을 그대로 사용하지 않고 필터링하는 과정이 필요하다.

---

## 10.1 정상 범위 검사

센서값이 물리적으로 말이 되지 않는 범위라면 오류로 판단한다.

| 센서    | 정상 범위 예시    |
| ----- | ----------- |
| 온도 센서 | -10℃ ~ 80℃  |
| 조도 센서 | 0 ~ 1023    |
| 거리 센서 | 2cm ~ 400cm |

예를 들어 거리 센서가 0을 반환하거나 400cm를 초과하면 측정 실패로 처리할 수 있다.

---

## 10.2 이동 평균 필터

센서값이 순간적으로 튀는 문제를 줄이기 위해 여러 번 측정한 평균값을 사용할 수 있다.

```cpp
int readAverageAnalog(int pin) {
  long sum = 0;

  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delay(5);
  }

  return sum / 10;
}
```

이동 평균을 사용하면 센서 노이즈를 줄일 수 있지만, 응답 속도는 조금 느려질 수 있다.

---

## 10.3 타임아웃 처리

초음파 거리 센서는 신호가 돌아오지 않는 경우가 있다.
이 경우 `pulseIn()`에 타임아웃을 설정하여 프로그램이 멈추지 않도록 한다.

```cpp
duration = pulseIn(echoPin, HIGH, 30000);
```

위 코드는 30ms 안에 신호가 돌아오지 않으면 측정 실패로 처리한다.

---

## 10.4 급격한 변화값 제한

이전 센서값과 현재 센서값의 차이가 너무 크면 오류일 가능성이 있다.

```cpp
if (abs(currentValue - previousValue) > 300) {
  currentValue = previousValue;
}
```

이 방식은 순간적인 튐 값을 제거하는 데 사용할 수 있다.

---

## 10.5 히스테리시스 적용

LED가 조건 경계값 근처에서 계속 켜졌다 꺼지는 문제를 막기 위해 히스테리시스를 적용할 수 있다.

예를 들어 조도 기준을 300 하나로만 두면, 값이 299와 301 사이에서 흔들릴 때 LED가 계속 변할 수 있다.
이때 켜지는 기준과 꺼지는 기준을 다르게 설정한다.

```text
LED ON 기준: 조도값 280 미만
LED OFF 기준: 조도값 350 초과
```

이렇게 하면 센서값이 조금 흔들려도 LED 상태가 불필요하게 반복 변경되지 않는다.

---

## 11. 센서 정확도와 응답 시간 고려

센서는 종류에 따라 정확도와 응답 시간이 다르다.

| 센서        | 고려사항                                  |
| --------- | ------------------------------------- |
| 온도 센서     | 주변 온도가 천천히 변하므로 빠르게 읽을 필요가 적다.        |
| 조도 센서     | 빛 변화에 비교적 빠르게 반응하지만 노이즈가 있을 수 있다.     |
| 초음파 거리 센서 | 물체 표면, 각도, 거리 범위에 따라 측정 오차가 발생할 수 있다. |

따라서 모든 센서를 너무 빠르게 읽기보다는 적절한 주기로 읽는 것이 좋다.
예를 들어 100~500ms 간격으로 센서를 읽으면 아두이노의 처리 부담을 줄이면서 안정적인 제어가 가능하다.

---

## 12. 리소스 제한을 고려한 코드 작성

아두이노 UNO는 메모리와 처리 속도가 제한적이다.
따라서 다음과 같은 방식으로 코드를 작성하는 것이 좋다.

| 고려사항         | 설명                                     |
| ------------ | -------------------------------------- |
| 함수 분리        | 센서 읽기, 에러 처리, LED 제어를 함수로 나누어 관리한다.    |
| 불필요한 문자열 줄이기 | Serial 출력이 너무 많으면 메모리와 속도에 영향을 줄 수 있다. |
| delay 사용 최소화 | 긴 delay는 센서 응답과 제어 속도를 늦춘다.            |
| 간단한 조건문 사용   | 복잡한 연산보다는 단순한 조건문을 사용한다.               |
| 배열 크기 제한     | 평균 필터 사용 시 너무 큰 배열을 사용하지 않는다.          |

---

## 13. 실행 결과 예시

실행 시 시리얼 모니터에는 다음과 같은 값이 출력된다.

```text
Temp: 24.35 C, Light: 420, Distance: 35.20 cm
Temp: 24.42 C, Light: 250, Distance: 12.80 cm
Temp: 31.10 C, Light: 180, Distance: 8.40 cm
```

예상 LED 동작은 다음과 같다.

| 센서 상태                    | LED 동작                |
| ------------------------ | --------------------- |
| 온도 낮음, 주변 어두움, 물체 멀리 있음  | 파란색 LED 밝게 점등         |
| 온도 보통, 주변 보통, 물체 가까움     | 초록색 LED 중간 밝기로 천천히 점멸 |
| 온도 높음, 주변 어두움, 물체 매우 가까움 | 빨간색 LED 밝게 빠른 점멸      |
| 센서 오류 발생                 | 보라색 LED 점등            |

---

## 14. 정리

본 문서에서는 아두이노에 온도 센서, 조도 센서, 거리 센서를 연결하고, 센서 데이터를 기반으로 RGB LED를 제어하는 방법을 정리하였다.

온도 센서는 LED 색상 결정에 사용하고, 조도 센서는 LED 밝기 결정에 사용하며, 거리 센서는 LED 점멸 속도 결정에 사용하였다.
또한 센서값의 오류를 줄이기 위해 정상 범위 검사, 이동 평균 필터, 타임아웃 처리, 급격한 변화값 제한, 히스테리시스 방법을 적용할 수 있음을 확인하였다.

아두이노는 제한된 메모리와 처리 속도를 가지므로, 센서 읽기 함수와 LED 제어 함수를 분리하고, 불필요한 연산을 줄이는 방식으로 효율적인 프로그램을 작성하는 것이 중요하다.

최종적으로 센서 입력, 데이터 처리, 조건 판단, LED 출력이 하나의 흐름으로 통합되어 동작하는 임베디드 제어 시스템을 구성할 수 있다.
