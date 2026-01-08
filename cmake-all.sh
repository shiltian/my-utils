#!/usr/bin/env bash

# llvm

cmake -G Ninja -DCMAKE_BUILD_TYPE=Release                                      \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX"                              \
      -DLLVM_ENABLE_PROJECTS="clang;lld;cross-project-tests"                   \
      -DLLVM_ENABLE_RUNTIMES="compiler-rt"                                     \
      -DLLVM_INSTALL_UTILS=ON                                                  \
      -DLLVM_INCLUDE_BENCHMARKS=OFF                                            \
      -DLLVM_INCLUDE_EXAMPLES=OFF                                              \
      -DLLVM_ENABLE_ASSERTIONS=ON                                              \
      -DLLVM_ENABLE_BINDINGS=OFF                                               \
      -DLLVM_ENABLE_OCAMLDOC=OFF                                               \
      -DLLVM_INCLUDE_DOCS=OFF                                                  \
      -DLLVM_USE_LINKER=mold                                                   \
      -DBUILD_SHARED_LIBS=ON                                                   \
      -B $BUILD_ROOT/llvm/release                                              \
      -S $HOME/Documents/vscode/llvm-project/llvm                              \
      --install-prefix=$BUILD_ROOT/llvm/release

cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug                                        \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX"                              \
      -DLLVM_ENABLE_PROJECTS="clang;lld;cross-project-tests"                   \
      -DLLVM_ENABLE_RUNTIMES="compiler-rt"                                     \
      -DLLVM_INSTALL_UTILS=ON                                                  \
      -DLLVM_INCLUDE_BENCHMARKS=OFF                                            \
      -DLLVM_INCLUDE_EXAMPLES=OFF                                              \
      -DLLVM_ENABLE_ASSERTIONS=ON                                              \
      -DLLVM_ENABLE_BINDINGS=OFF                                               \
      -DLLVM_ENABLE_OCAMLDOC=OFF                                               \
      -DLLVM_INCLUDE_DOCS=OFF                                                  \
      -DLLVM_OPTIMIZED_TABLEGEN=ON                                             \
      -DLLVM_USE_LINKER=mold                                                   \
      -DBUILD_SHARED_LIBS=ON                                                   \
      -B $BUILD_ROOT/llvm/debug                                                \
      -S $HOME/Documents/vscode/llvm-project/llvm                              \
      --install-prefix=$BUILD_ROOT/llvm/debug

# lightning-llvm

cmake -G Ninja                                                                 \
      -DCMAKE_BUILD_TYPE=Release                                               \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
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
      -DLLVM_USE_LINKER=mold                                                   \
      -B $BUILD_ROOT/lightning-llvm/release                                    \
      -S $HOME/Documents/vscode/internal/llvm-project/llvm                     \
      --install-prefix=$BUILD_ROOT/lightning-llvm/release


cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug                                        \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
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
      -DLLVM_OPTIMIZED_TABLEGEN=ON                                             \
      -DLLVM_USE_LINKER=mold                                                   \
      -B $BUILD_ROOT/lightning-llvm/debug                                      \
      -S $HOME/Documents/vscode/internal/llvm-project/llvm                     \
      --install-prefix=$BUILD_ROOT/lightning-llvm/debug

# device-libs

cmake -G Ninja -DCMAKE_BUILD_TYPE=Release                                      \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON                                       \
      -DLLVM_ROOT=$BUILD_ROOT/lightning-llvm/release                           \
      -DClang_ROOT=$BUILD_ROOT/lightning-llvm/release                          \
      -B $BUILD_ROOT/device-libs/release                                       \
      -S $HOME/Documents/vscode/internal/llvm-project/amd/device-libs

# comgr

cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug                                        \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON                                       \
      -DAMDDeviceLibs_ROOT=$BUILD_ROOT/device-libs/release                     \
      -DClang_ROOT=$BUILD_ROOT/lightning-llvm/debug                            \
      -DLLD_ROOT=$BUILD_ROOT/lightning-llvm/debug                              \
      -DCOMGR_BUILD_SHARED_LIBS=ON                                             \
      -DCOMGR_DISABLE_SPIRV=ON                                                 \
      -B $BUILD_ROOT/comgr/debug                                               \
      -S $HOME/Documents/vscode/internal/llvm-project/amd/comgr                \
      --install-prefix=$BUILD_ROOT/comgr/debug

cmake -G Ninja -DCMAKE_BUILD_TYPE=Release                                      \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON                                       \
      -DAMDDeviceLibs_ROOT=$BUILD_ROOT/device-libs/release                     \
      -DClang_ROOT=$BUILD_ROOT/lightning-llvm/release                          \
      -DLLD_ROOT=$BUILD_ROOT/lightning-llvm/release                            \
      -DCOMGR_BUILD_SHARED_LIBS=ON                                             \
      -DCOMGR_DISABLE_SPIRV=ON                                                 \
      -B $BUILD_ROOT/comgr/release                                             \
      -S $HOME/Documents/vscode/internal/llvm-project/amd/comgr                \
      --install-prefix=$BUILD_ROOT/comgr/release

# offload

cmake -G Ninja -DCMAKE_BUILD_TYPE=Release                                      \
      -DCMAKE_C_COMPILER_LAUNCHER=ccache                                       \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache                                     \
      -DCMAKE_C_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang                  \
      -DCMAKE_CXX_COMPILER=/home/linuxbrew/.linuxbrew/bin/clang++              \
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX"                              \
      -DLLVM_ENABLE_PROJECTS="clang;lld;compiler-rt"                           \
      -DLLVM_ENABLE_RUNTIMES="openmp;offload"                                  \
      -DBUILD_SHARED_LIBS=ON                                                   \
      -DLLVM_INSTALL_UTILS=ON                                                  \
      -DLLVM_INCLUDE_BENCHMARKS=OFF                                            \
      -DLLVM_INCLUDE_EXAMPLES=OFF                                              \
      -DLLVM_ENABLE_ASSERTIONS=ON                                              \
      -DLLVM_APPEND_VC_REV=OFF                                                 \
      -DLLVM_ENABLE_BINDINGS=OFF                                               \
      -DLLVM_ENABLE_OCAMLDOC=OFF                                               \
      -DLLVM_INCLUDE_DOCS=OFF                                                  \
      -DLLVM_ENABLE_LLD=ON                                                     \
      -DRUNTIMES_CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Debug;-DLIBOMPTARGET_PLUGINS_TO_BUILD=amdgpu;nvptx;-DLIBOMPTARGET_DLOPEN_PLUGINS='';-DLIBOMPTARGET_ENABLE_DEBUG=ON" \
      -B $BUILD_ROOT/offload/release                                           \
      -S $HOME/Documents/vscode/llvm-project/llvm                              \
      --install-prefix=$BUILD_ROOT/offload/release
