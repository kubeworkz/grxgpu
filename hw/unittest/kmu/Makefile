ROOT_DIR := $(realpath ../../..)
include $(ROOT_DIR)/config.mk

PROJECT := kmu

RTL_DIR := $(VORTEX_HOME)/hw/rtl
DPI_DIR := $(VORTEX_HOME)/hw/dpi

SRC_DIR := $(VORTEX_HOME)/hw/unittest/$(PROJECT)

CXXFLAGS := -I$(SRC_DIR) -I$(VORTEX_HOME)/hw/unittest/common -I$(SW_COMMON_DIR)
CXXFLAGS += -I$(ROOT_DIR)/sw -I$(ROOT_DIR)/hw

SRCS := $(SRC_DIR)/main.cpp

DBG_TRACE_FLAGS :=

RTL_PKGS := $(RTL_DIR)/VX_gpu_pkg.sv
RTL_PKGS += $(RTL_DIR)/dxa/VX_dxa_pkg.sv $(RTL_DIR)/tcu/VX_tcu_pkg.sv
RTL_PKGS += $(RTL_DIR)/VX_trace_pkg.sv


RTL_INCLUDE := -I$(ROOT_DIR)/sw -I$(ROOT_DIR)/hw -I$(RTL_DIR) -I$(DPI_DIR) -I$(RTL_DIR)/libs -I$(VORTEX_HOME)/hw/unittest/kmu
RTL_INCLUDE += -I$(RTL_DIR)/interfaces -I$(RTL_DIR)/mem -I$(RTL_DIR)/fpu -I$(RTL_DIR)/core
RTL_INCLUDE += -I$(RTL_DIR)/dxa -I$(RTL_DIR)/tcu -I$(RTL_DIR)/tcu/tfr -I$(RTL_DIR)/tcu/dpi
RTL_INCLUDE += -I$(RTL_DIR)/tcu/fpnew -I$(RTL_DIR)/tcu/dsp -I$(RTL_DIR)/tcu/bhf

TOP := VX_kmu_top

include ../common.mk

# VX_trace_pkg references the DXA/TCU packages; this bench does not
# instantiate those engines, so their public params have no local use.
VL_FLAGS += -Wno-UNUSEDPARAM
