# Embedded Linux Study

임베디드 시스템과 Arduino 경험을 바탕으로 임베디드 리눅스의 구조와 개발 과정을 학습하기 위한 공간입니다.

## 학습 목표

- 임베디드 리눅스 시스템의 부팅 구조 이해
- Linux 명령어와 셸 사용 능력 확보
- 크로스 컴파일과 툴체인 이해
- 부트로더, 커널, Device Tree, Root Filesystem의 역할 이해
- GPIO, UART, I2C, SPI 장치 제어 실습
- 사용자 공간 프로그램과 Linux Device Driver의 차이 이해
- Buildroot 또는 Yocto 기반 이미지 생성 경험

## 전체 학습 흐름

```text
Linux 기초
  ↓
임베디드 리눅스 구성요소
  ↓
크로스 컴파일
  ↓
부팅 과정과 U-Boot
  ↓
Linux Kernel과 Device Tree
  ↓
GPIO/UART/I2C/SPI 제어
  ↓
Device Driver
  ↓
Buildroot/Yocto 시스템 이미지 제작
  ↓
통합 프로젝트
```

## 권장 학습 순서

### 1. Linux 기초

- 파일과 디렉터리 구조
- 권한과 사용자
- 프로세스와 스레드
- 셸 명령어와 Bash
- SSH, SCP, 네트워크 기초
- `systemd`, 로그 및 서비스 관리

### 2. 임베디드 리눅스 구조

- Host PC와 Target Board
- Bootloader
- Linux Kernel
- Device Tree
- Root Filesystem
- 응용 프로그램

### 3. 개발 환경

- GCC와 Makefile
- ARM 크로스 컴파일러
- 정적/동적 라이브러리
- CMake 기초
- GDB 및 원격 디버깅

### 4. 하드웨어 인터페이스

- GPIO LED 및 버튼
- UART 통신
- I2C 센서
- SPI 장치
- PWM 제어
- `/dev`, `/sys`, `/proc` 인터페이스

### 5. 커널과 드라이버

- Kernel Module
- Character Device Driver
- Platform Driver
- Device Tree 바인딩
- Interrupt 처리
- 동기화와 커널 메모리

### 6. 시스템 빌드

- Buildroot
- Yocto Project
- Root Filesystem 구성
- 부팅 이미지 생성
- 패키지와 서비스 자동 실행

## 첫 번째 실습 프로젝트

보드의 GPIO에 연결된 LED와 버튼을 Linux 사용자 공간에서 제어합니다.

```text
Button 입력
  ↓
GPIO 상태 읽기
  ↓
C 프로그램 판단
  ↓
LED 출력 변경
  ↓
로그 기록
```

이후 동일 기능을 Linux Device Driver 방식으로 다시 구현해 사용자 공간 제어와 커널 드라이버의 차이를 비교합니다.

## 준비 장비 후보

- Raspberry Pi 또는 Raspberry Pi Compute Module
- BeagleBone Black
- STM32MP1 계열 보드
- NVIDIA Jetson 계열 보드
- USB-UART 변환기
- LED, 버튼, 저항, I2C/SPI 센서

사용할 보드가 결정되면 보드에 맞춰 툴체인, 핀맵, 이미지 설치 방법 및 실습 코드를 추가합니다.

