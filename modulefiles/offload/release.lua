-- -*- lua -*-
local base = myFileName():match("(.*)/[^/]+/[^/]+%.lua$")
local pkg_home = loadfile(pathJoin(base, ".common", "llvm_base.lua"))()

-- offload-specific: additional arch-qualified lib paths
prepend_path("LIBRARY_PATH",      pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
prepend_path("LD_LIBRARY_PATH",   pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
prepend_path("DYLD_LIBRARY_PATH", pathJoin(pkg_home, "lib", "x86_64-unknown-linux-gnu"))
