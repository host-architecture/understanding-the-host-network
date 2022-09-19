obj-m   := miomap.o
KDIR    := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd) 
  
all: 
		$(MAKE) -C $(KDIR) M=${PWD} SUBDIRS=$(PWD) modules