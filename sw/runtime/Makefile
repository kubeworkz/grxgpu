ROOT_DIR := $(realpath ../..)
include $(ROOT_DIR)/config.mk

all: stub rtlsim simx opae xrt rv64chip

vm: stub simx

stub:
	$(MAKE) -C stub

simx:
	$(MAKE) -C simx

rtlsim:
	$(MAKE) -C rtlsim

opae:
	$(MAKE) -C opae

xrt:
	$(MAKE) -C xrt

rv64chip:
	$(MAKE) -C rv64chip

clean:
	$(MAKE) -C stub clean
	$(MAKE) -C simx clean
	$(MAKE) -C rtlsim clean
	$(MAKE) -C opae clean
	$(MAKE) -C xrt clean
	$(MAKE) -C rv64chip clean

.PHONY: all stub simx rtlsim opae xrt rv64chip clean
