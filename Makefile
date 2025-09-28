# These settings can be adjusted as needed to fit your project structure
PROJECT_NAME := teeny_ws

ifndef PROJECT_NAME
  $(error "PROJECT_NAME is not set. Please update the Makefile appropriately.")
endif

# These settings should ideally remain unchanged
SHELL := /bin/zsh
GIT_URL := https://github.com/vamship
COMPILER := mpy-cross
DOC_GENERATOR := pdoc
SRC_DIR := src/${PROJECT_NAME}
BUILD_DIR := build
DOCS_DIR := docs

SOURCES := $(shell find ${SRC_DIR} -name '*.py')
INTERMEDIATE_FILES := $(shell find ${SRC_DIR} -name '*.pyc')
BUILD_TARGETS := $(patsubst %.py,%.mpy,${SOURCES})
BUILD_TARGETS := $(patsubst ${SRC_DIR}/%,${BUILD_DIR}/%,$(BUILD_TARGETS))

.PHONY: docs

all: build

help:
	@echo "================== Targets ==================="
	@echo "clean              : Remove intermediate files (e.g., .pyc files)"
	@echo "build              : Compile all .py files to .mpy"
	@echo "docs               : Generate project documentation"
	@echo
	@echo "Advanced Operations: "
	@echo "clean-build        : Remove build files"
	@echo "clean-docs         : Remove generated documentation"
	@echo

info:
	@echo "================ Project Info ================"
	@echo "Project            : ${PROJECT_NAME}"
	@echo "Source Control URL : ${GIT_URL}/${PROJECT_NAME}"
	@echo "Source Path        : ${SRC_DIR}"
	@echo "Build Path         : ${BUILD_DIR}"
	@echo "Documentation Path : ${BUILD_DIR}"
	@echo "Compiler           : ${COMPILER}"
	@echo "Doc Generator      : ${DOC_GENERATOR}"

docs:
	@echo -n "Generating documentation ... "
	@${DOC_GENERATOR} --output-dir ${DOCS_DIR} \
		--edit-url ${PROJECT_NAME}=${GIT_URL}/${PROJECT_NAME}/blob/main/src/${PROJECT_NAME}/ \
		${SRC_DIR}
	@echo "Done"

clean: clean-intermediate
	@echo "Done"

clean-build:
	@echo -n "Cleaning build directory ... "
	@rm -rf build
	@echo "OK"

clean-docs:
	@echo -n "Cleaning documentation directory ... "
	@rm -rf ${DOCS_DIR}
	@echo "OK"

clean-intermediate:
	@echo -n "Cleaning intermediate files ... "
	@rm -f ${INTERMEDIATE_FILES}
	@echo "OK"

build: compile # This is there because make treats 'build' specially

compile: ${BUILD_TARGETS}
	@echo "Build Complete"

# Pattern rule to compile .py files to .mpy files
${BUILD_TARGETS}: ${BUILD_DIR}/%.mpy: ${SRC_DIR}/%.py
	@echo "Compiling [$<] --> [$@]"
	@mkdir -p $(dir $@)
	@${COMPILER} -o ${@} -- ${<}