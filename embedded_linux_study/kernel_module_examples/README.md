# 커널 모듈 및 문자 장치 드라이버 예제

이 디렉터리는 다음 두 외부(out-of-tree) 커널 모듈을 빌드한다.

- `hello_module.c`: 적재/제거와 모듈 매개변수만 실습하는 일반 모듈
- `simple_char_driver.c`: `/dev/edu_char`를 등록하는 교육용 misc 문자 장치 드라이버

## 빌드

실행 중인 커널과 정확히 일치하는 헤더가 필요하다.

```bash
sudo apt install build-essential linux-headers-$(uname -r)
make
```

다른 커널 트리를 사용할 때는 다음과 같이 지정한다.

```bash
make KDIR=/path/to/prepared/kernel/build
```

ARM64 크로스 컴파일 예:

```bash
make KDIR=/path/to/raspberrypi/kernel \
    ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
```

## 시험

```bash
sudo insmod hello_module.ko message="test message"
dmesg | tail
sudo rmmod hello_module

sudo insmod simple_char_driver.ko
printf 'hello driver\n' | sudo tee /dev/edu_char >/dev/null
sudo cat /dev/edu_char
sudo rmmod simple_char_driver
```

`simple_char_driver`의 장치 모드는 `0600`이므로 root만 읽고 쓸 수 있다. 제품에서는 udev 규칙과 전용 그룹으로 필요한 사용자에게만 권한을 부여한다.

## 주의

- 가상 머신 또는 복구 가능한 시험 보드에서 먼저 실행한다.
- `dmesg -w`를 켜고 경고와 Oops를 관찰한다.
- 강제 적재/제거 옵션을 사용하지 않는다.
- 이 예제는 실제 레지스터, IRQ 또는 GPIO를 제어하지 않는다.
- Windows에서는 직접 빌드되지 않으며 Linux 커널 빌드 환경이 필요하다.

