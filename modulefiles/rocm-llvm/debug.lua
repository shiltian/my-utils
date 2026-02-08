-- -*- lua -*-

whatis("Name    : rocm-llvm")
whatis("Version : debug")

-- Define all conflicting modules
local conflicts = {"llvm", "lightning-llvm", "offload", "rocm-llvm"}

-- Automatically unload conflicting modules if they are loaded
for _, mod in ipairs(conflicts) do
    if isloaded(mod) then
        unload(mod)
    end
end

-- Declare conflicts
conflict(table.unpack(conflicts))

local build_root = os.getenv("BUILD_ROOT")
local pkg_home = pathJoin(build_root, myModuleName(), myModuleVersion())

pushenv("LLVM_ROOT", pkg_home)
pushenv("LLVM_PATH", pkg_home)

prepend_path("PATH",              pathJoin(pkg_home, "bin"))
prepend_path("CPATH",             pathJoin(pkg_home, "include"))
prepend_path("LIBRARY_PATH",      pathJoin(pkg_home, "lib"))
prepend_path("LD_LIBRARY_PATH",   pathJoin(pkg_home, "lib"))
prepend_path("DYLD_LIBRARY_PATH", pathJoin(pkg_home, "lib"))
