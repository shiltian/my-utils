-- -*- lua -*-

whatis("Name    : offload")
whatis("Version : release")

conflict("llvm", "lightning-llvm", "offload")

local build_root = os.getenv("BUILD_ROOT")
local pkg_home = pathJoin(build_root, myModuleName(), myModuleVersion())

pushenv("LLVM_ROOT", pkg_home)
pushenv("LLVM_PATH", pkg_home)

prepend_path("PATH",              pathJoin(pkg_home, "bin"))
prepend_path("CPATH",             pathJoin(pkg_home, "include"))
prepend_path("LIBRARY_PATH",      pathJoin(pkg_home, "lib"))
prepend_path("LIBRARY_PATH",      pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
prepend_path("LD_LIBRARY_PATH",   pathJoin(pkg_home, "lib"))
prepend_path("LD_LIBRARY_PATH",   pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
prepend_path("DYLD_LIBRARY_PATH", pathJoin(pkg_home, "lib"))
prepend_path("DYLD_LIBRARY_PATH", pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
