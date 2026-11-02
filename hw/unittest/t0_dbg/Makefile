ROOT_DIR := $(realpath ../../..)
include $(ROOT_DIR)/config.mk

PROJECT := t0_dbg

RTL_DIR := $(VORTEX_HOME)/hw/rtl
DPI_DIR := $(VORTEX_HOME)/hw/dpi

SRC_DIR := $(VORTEX_HOME)/hw/unittest/$(PROJECT)

CXXFLAGS := -I$(SRC_DIR) -I$(VORTEX_HOME)/hw/unittest/common -I$(SW_COMMON_DIR)
CXXFLAGS += -I$(THIRD_PARTY_DIR)/softfloat/source/include
CXXFLAGS += -I$(ROOT_DIR)/sw -I$(ROOT_DIR)/hw

LDFLAGS += $(THIRD_PARTY_DIR)/softfloat/build/Linux-x86_64-GCC/softfloat.a

VL_FLAGS += -DSV_DPI
# The core's existing RTL carries lint warnings unrelated to the T0 wrapper;
# keep them visible without failing the build, as the full rtlsim target does.
VL_FLAGS += -Wno-fatal

SRCS := $(DPI_DIR)/dpi_util.cpp
SRCS += $(DPI_DIR)/dpi_float.cpp
SRCS += $(SW_COMMON_DIR)/softfloat_ext.cpp
SRCS += $(SW_COMMON_DIR)/rvfloats.cpp
SRCS += $(SRC_DIR)/main.cpp

DBG_TRACE_FLAGS :=

RTL_PKGS := $(RTL_DIR)/VX_gpu_pkg.sv
RTL_PKGS += $(RTL_DIR)/fpu/VX_fpu_pkg.sv
RTL_PKGS += $(RTL_DIR)/dxa/VX_dxa_pkg.sv
RTL_PKGS += $(RTL_DIR)/tcu/VX_tcu_pkg.sv

RTL_INCLUDE := -I$(ROOT_DIR)/sw -I$(ROOT_DIR)/hw -I$(RTL_DIR) -I$(DPI_DIR) -I$(RTL_DIR)/libs
RTL_INCLUDE += -I$(RTL_DIR)/interfaces -I$(RTL_DIR)/mem -I$(RTL_DIR)/dbg -I$(SRC_DIR)
RTL_INCLUDE += -I$(RTL_DIR)/core -I$(RTL_DIR)/fpu -I$(RTL_DIR)/dxa -I$(RTL_DIR)/tex -I$(RTL_DIR)/om -I$(RTL_DIR)/tcu
RTL_INCLUDE += -I$(RTL_DIR)/tcu/tfr -I$(RTL_DIR)/tcu/dpi -I$(RTL_DIR)/tcu/fpnew -I$(RTL_DIR)/tcu/dsp -I$(RTL_DIR)/tcu/bhf

CROSS := $(RISCV_TOOLCHAIN_PATH)/bin/$(RISCV_PREFIX)-
IMAGE_ELF := $(CURDIR)/t0_image.elf
IMAGE_BIN := $(CURDIR)/t0_image.bin
SHORT_IMAGE_ELF := $(CURDIR)/t0_short_image.elf
SHORT_IMAGE_BIN := $(CURDIR)/t0_short_image.bin

CXXFLAGS += -DT0_IMAGE_PATH=\"$(IMAGE_BIN)\"
CXXFLAGS += -DT0_SHORT_IMAGE_PATH=\"$(SHORT_IMAGE_BIN)\"

TOP := VX_t0_dbg_tb_top

include ../common.mk

$(DESTDIR)/$(PROJECT): $(IMAGE_BIN) $(SHORT_IMAGE_BIN)

# The image is assembled and linked at the core's startup PC, then flattened
# for the SBA loader.
$(IMAGE_BIN): $(SRC_DIR)/t0_image.S
	@if [ ! -x "$(CROSS)gcc" ]; then \
		echo "error: RISC-V toolchain not found at $(CROSS)gcc"; \
		echo "       set RISCV_TOOLCHAIN_PATH or TOOLDIR"; \
		exit 1; \
	fi
	$(CROSS)gcc -march=rv32i_zicsr -mabi=ilp32 -nostdlib -nostartfiles \
		-Wl,-Ttext=0x80000000 -Wl,-e,_start -Wl,--build-id=none \
		-o $(IMAGE_ELF) $<
	$(CROSS)objcopy -O binary $(IMAGE_ELF) $@

$(SHORT_IMAGE_BIN): $(SRC_DIR)/t0_short_image.S
	@if [ ! -x "$(CROSS)gcc" ]; then \
		echo "error: RISC-V toolchain not found at $(CROSS)gcc"; \
		echo "       set RISCV_TOOLCHAIN_PATH or TOOLDIR"; \
		exit 1; \
	fi
	$(CROSS)gcc -march=rv32i_zicsr -mabi=ilp32 -nostdlib -nostartfiles \
		-Wl,-Ttext=0x80000000 -Wl,-e,_start -Wl,--build-id=none \
		-o $(SHORT_IMAGE_ELF) $<
	$(CROSS)objcopy -O binary $(SHORT_IMAGE_ELF) $@

clean: clean-image

clean-image:
	rm -f $(IMAGE_ELF) $(IMAGE_BIN) $(SHORT_IMAGE_ELF) $(SHORT_IMAGE_BIN)
