#!/usr/bin/env bash

SRC_ROOT=$1
BUILD_ROOT=$2
INSTALL_ROOT=$3

cmake -G Ninja                                                                 \
      -DCMAKE_BUILD_TYPE=Release                                               \
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU"                                    \
      -DLLVM_ENABLE_PROJECTS="clang;lld;cross-project-tests"                   \
      -DLLVM_ENABLE_RUNTIMES="compiler-rt"                                     \
      -DLLVM_INSTALL_UTILS=ON                                                  \
      -DLLVM_INCLUDE_BENCHMARKS=OFF                                            \
      -DLLVM_INCLUDE_EXAMPLES=OFF                                              \
      -DLLVM_ENABLE_ASSERTIONS=ON                                              \
      -DLLVM_ENABLE_BINDINGS=OFF                                               \
      -DLLVM_ENABLE_OCAMLDOC=OFF                                               \
      -DLLVM_INCLUDE_DOCS=OFF                                                  \
      -B $BUILD_ROOT                                                           \
      -S $SRC_ROOT/llvm                                                        \
      --install-prefix=$INSTALL_ROOT

cmake --build $BUILD_ROOT --target install
