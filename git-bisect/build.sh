#!/bin/bash

# Exit on any error

cd $BUILD_ROOT/llvm/release

rm -rf *

cmake -G Ninja -DCMAKE_BUILD_TYPE=Release                                      \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX"                              \
      -DLLVM_ENABLE_PROJECTS="clang;lld"                                       \
      -DLLVM_ENABLE_RUNTIMES="compiler-rt"                                     \
      -DLLVM_INSTALL_UTILS=ON                                                  \
      -DLLVM_INCLUDE_BENCHMARKS=OFF                                            \
      -DLLVM_INCLUDE_EXAMPLES=OFF                                              \
      -DLLVM_ENABLE_ASSERTIONS=ON                                              \
      -DLLVM_ENABLE_BINDINGS=OFF                                               \
      -DLLVM_ENABLE_OCAMLDOC=OFF                                               \
      -DLLVM_INCLUDE_DOCS=OFF                                                  \
      -DLLVM_ENABLE_LLD=ON                                                     \
      -B $BUILD_ROOT/llvm/release                                              \
      -S $HOME/Documents/vscode/llvm-project/llvm                              \
      --install-prefix=$BUILD_ROOT/llvm/release

ninja install
