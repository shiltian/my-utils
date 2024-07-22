-- -*- lua -*-

whatis("Name    : comgr")
whatis("Version : debug")

conflict("comgr")

local build_root = os.getenv("BUILD_ROOT")
local pkg_home = pathJoin(build_root, myModuleName(), myModuleVersion())

prepend_path("CPATH",             pathJoin(pkg_home, "include"))
prepend_path("LIBRARY_PATH",      pathJoin(pkg_home, "lib"))
prepend_path("LD_LIBRARY_PATH",   pathJoin(pkg_home, "lib"))
prepend_path("DYLD_LIBRARY_PATH", pathJoin(pkg_home, "lib"))
