obj-m += hello_module.o
obj-m += simple_char_driver.o

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

.PHONY: all clean install

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install

