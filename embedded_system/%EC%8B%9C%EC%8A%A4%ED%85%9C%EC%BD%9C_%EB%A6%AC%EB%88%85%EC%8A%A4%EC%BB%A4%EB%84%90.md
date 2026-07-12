
# 시스템 콜과 리눅스 커널

## 1. 시스템 콜의 기본 개념과 중요성

### 시스템 콜(System Call)이란?
시스템 콜은 **사용자 모드(User Mode)**에서 실행 중인 애플리케이션이 **커널 모드(Kernel Mode)**에 접근할 수 있도록 하는 **인터페이스**입니다. 즉, 사용자 프로그램이 파일 시스템, 메모리, 프로세스 관리, 네트워크 등 **운영체제 자원에 접근**하기 위한 **유일한 통로**입니다.

### 왜 중요한가?
- **보안성** 확보: 사용자 프로그램이 직접 커널을 조작하지 않도록 막음.
- **안정성** 제공: 커널 내부 구조를 은닉함으로써 운영체제의 안정성을 높임.
- **표준화된 인터페이스** 제공: 다양한 하드웨어 환경에서 동일한 API 제공 가능.

## 2. 리눅스에서 일반적인 시스템 콜

- `read()`: 파일이나 장치에서 데이터를 읽음
- `write()`: 파일이나 장치에 데이터를 씀
- `open()`: 파일을 열거나 생성
- `close()`: 파일 디스크립터를 닫음
- `fork()`: 프로세스 생성
- `exec()`: 새 프로그램 실행
- `wait()`: 자식 프로세스가 종료될 때까지 대기
- `exit()`: 현재 프로세스를 종료
- `ioctl()`: 장치 제어 명령

## 3. 시스템 콜의 종류와 용도

### 파일 관련 시스템 콜
| 시스템 콜 | 용도 |
|-----------|------|
| `open()`  | 파일 열기 |
| `read()`  | 파일에서 데이터 읽기 |
| `write()` | 파일에 데이터 쓰기 |
| `close()` | 파일 닫기 |
| `lseek()` | 파일 포인터 위치 이동 |

### 프로세스 관련 시스템 콜
| 시스템 콜 | 용도 |
|-----------|------|
| `fork()`  | 자식 프로세스 생성 |
| `exec()`  | 다른 프로그램 실행 |
| `wait()`  | 자식 프로세스 종료 대기 |
| `exit()`  | 프로세스 종료 |

## 4. 커널 인터페이스와 시스템 콜의 관계

- 사용자 공간과 커널 공간은 메모리 보호를 위해 분리되어 있음.
- 시스템 콜을 호출하면 **인터럽트 (보통 `int 0x80`)** 또는 **`syscall` 명령어**를 통해 커널로 진입.
- 커널은 시스템 콜 번호를 기반으로 알맞은 커널 함수를 실행함.

## 5. 커널 모듈과 시스템 콜의 상호작용

- **커널 모듈**은 커널 공간에서 실행되는 코드로, 장치 드라이버나 추가 기능을 모듈 형태로 삽입 가능.
- 커널 모듈은 기존 시스템 콜을 후킹하거나, 새로운 시스템 콜을 정의하여 기능을 확장할 수 있음.
- 예: 새로운 파일 조작 방법, 특수한 디바이스 제어 등

## 6. 사용자 영역 vs 커널 영역에서 시스템 콜 이용

| 구분 | 사용자 영역 | 커널 영역 (모듈) |
|------|-------------|------------------|
| 접근 방식 | 라이브러리 함수 호출 (ex. `fopen`) | `sys_call_table` 접근 또는 내부 함수 사용 |
| 예시 | `open("file.txt", O_RDONLY)` | `filp_open()` 사용 |
| 목적 | 커널 기능 요청 | 내부 기능 추가 또는 후킹 |
| 위험성 | 낮음 (보호됨) | 높음 (시스템 불안정 유발 가능) |

## 7. 예제: 커널 모듈에서 시스템 콜처럼 파일 열기

```c
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/init.h>

static int __init my_module_init(void) {
    struct file *f;
    mm_segment_t old_fs;
    char buf[128];
    loff_t pos = 0;

    printk(KERN_INFO "모듈 로딩됨\n");

    old_fs = get_fs();
    set_fs(KERNEL_DS);

    f = filp_open("/etc/hostname", O_RDONLY, 0);
    if (IS_ERR(f)) {
        printk(KERN_ERR "파일 열기 실패\n");
        return -1;
    }

    kernel_read(f, buf, sizeof(buf)-1, &pos);
    buf[127] = '\0';
    printk(KERN_INFO "읽은 내용: %s\n", buf);

    filp_close(f, NULL);
    set_fs(old_fs);

    return 0;
}

static void __exit my_module_exit(void) {
    printk(KERN_INFO "모듈 제거됨\n");
}

module_init(my_module_init);
module_exit(my_module_exit);
MODULE_LICENSE("GPL");
```

## 참고 문헌

- [Linux Kernel Development - Robert Love](https://www.kernel.org/doc/html/latest/)
- [Linux System Calls - The Linux Programming Interface, Michael Kerrisk](https://man7.org/tlpi/)
- [LWN: Adding a system call to Linux](https://lwn.net/Articles/604287/)
- [Linux Device Drivers, O'Reilly](https://lwn.net/Kernel/LDD3/)
