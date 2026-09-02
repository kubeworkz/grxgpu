ROOT_DIR := $(realpath ../../..)
include $(ROOT_DIR)/config.mk

CONFIGS := $(if $(findstring -DVX_CFG_EXT_TCU_ENABLE,$(CONFIGS)),$(CONFIGS),$(CONFIGS) -DVX_CFG_EXT_TCU_ENABLE)
CONFIGS := $(if $(findstring -DVX_CFG_EXT_DXA_ENABLE,$(CONFIGS)),$(CONFIGS),$(CONFIGS) -DVX_CFG_EXT_DXA_ENABLE)

PROJECT := sgemm_tcu_bf16

# Reuse source from sgemm_tcu_wg_dxa (format-agnostic via ITYPE/OTYPE)
WGDXA_DIR := $(VORTEX_HOME)/tests/regression/sgemm_tcu_wg_dxa
SRC_DIR := $(VORTEX_HOME)/tests/regression/$(PROJECT)

SRCS := $(WGDXA_DIR)/main.cpp $(SW_COMMON_DIR)/rvfloats.cpp $(SW_COMMON_DIR)/softfloat_ext.cpp
VX_SRCS := $(WGDXA_DIR)/kernel.cpp

# bf16 format: ITYPE=bf16, OTYPE=fp32
CONFIGS += -DITYPE=bf16 -DOTYPE=fp32

CONFIGS := $(if $(findstring -DVX_CFG_NUM_WARPS=,$(CONFIGS)),$(CONFIGS),$(CONFIGS) -DVX_CFG_NUM_WARPS=4)
CONFIGS := $(if $(findstring -DVX_CFG_ISSUE_WIDTH=,$(CONFIGS)),$(CONFIGS),$(CONFIGS) -DVX_CFG_ISSUE_WIDTH=4)
CONFIGS += -DVX_CFG_TCU_WGMMA_ENABLE
CONFIGS := $(if $(findstring -DWGMMA_SS,$(CONFIGS)),$(CONFIGS),$(CONFIGS) -DWGMMA_RS)
CONFIGS += -DWGMMA_DXA_DOUBLE_BUFFER

CXXFLAGS += -I$(THIRD_PARTY_DIR)/softfloat/source/include

LDFLAGS += $(THIRD_PARTY_DIR)/softfloat/build/Linux-x86_64-GCC/softfloat.a

KERNEL_LIB := vortex2

include ../common.mk
