-- -*- lua -*-
local base = myFileName():match("(.*)/[^/]+/[^/]+%.lua$")
loadfile(pathJoin(base, ".common", "llvm_base.lua"))()
