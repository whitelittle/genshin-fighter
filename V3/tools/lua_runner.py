import ctypes,sys
from pathlib import Path
lib=ctypes.CDLL('liblua5.4.so.0')
lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
lib.luaL_loadbufferx.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)];lib.lua_tolstring.restype=ctypes.c_char_p
L=lib.luaL_newstate();lib.luaL_openlibs(L)
s=Path(sys.argv[1]).read_text()
if len(sys.argv)>2:s=s[:s.index('local POOLS = {img = 256')]+Path(sys.argv[2]).read_text()
b=s.encode();r=lib.luaL_loadbufferx(L,b,len(b),b'task',None)
if r==0 and len(sys.argv)>2:r=lib.lua_pcallk(L,0,0,0,0,None)
if r:print(lib.lua_tolstring(L,-1,None).decode());sys.exit(1)
print('Lua OK')
