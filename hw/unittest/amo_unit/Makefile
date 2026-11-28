ROOT_DIR := $(realpath ../../..)
include $(ROOT_DIR)/config.mk

PROJECT := amo_unit

RTL_DIR := $(VORTEX_HOME)/hw/rtl
SRC_DIR := $(VORTEX_HOME)/hw/unittest/$(PROJECT)

# Reservation geometry shared with the testbench, so it derives the module's own
# hold deadline (AMO_TURNAROUND * (NUM_HARTS + 1)) instead of hard-coding it.
AMO_TURNAROUND ?= 64
NUM_RES_ENTRIES ?= 4

CONFIGS += -DSIMULATION

CXXFLAGS := -I$(SRC_DIR) -I$(VORTEX_HOME)/hw/unittest/common -I$(SW_COMMON_DIR)
CXXFLAGS += -I$(ROOT_DIR)/sw
CXXFLAGS += -DAMO_TURNAROUND=$(AMO_TURNAROUND)

SRCS += $(SRC_DIR)/main.cpp

RTL_PKGS := $(RTL_DIR)/VX_gpu_pkg.sv
RTL_INCLUDE := -I$(RTL_DIR)/cache -I$(RTL_DIR)/libs

# hw/rtl holds the shared headers; -I$(ROOT_DIR)/hw the generated VX_config.vh,
# whose hart-id width sets the deadline.
VL_FLAGS += -I$(RTL_DIR) -I$(ROOT_DIR)/hw

PARAMS := -GNUM_RES_ENTRIES=$(NUM_RES_ENTRIES) -GAMO_TURNAROUND=$(AMO_TURNAROUND)

TOP := VX_amo_unit

include ../common.mk
