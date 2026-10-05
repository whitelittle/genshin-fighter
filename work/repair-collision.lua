-- Editable initial profiles: local coordinates originate at the feet.
local Collision={results={},profiles={},moves={}}
for role=1,45 do Collision.profiles[role]={push=26,width=26,height=166,crouch=94}end
for _,role in ipairs({5,19,39})do Collision.profiles[role]={push=25,width=25,height=146,crouch=84}end
Collision.profiles[11]={push=42,width=40,height=202,crouch=130}
function Collision.world(a,l,b,r,t)
 if a.face<0 then l,r=-r,-l end
 return {a.x+l,a.y+b,a.x+r,a.y+t}
end
function Collision.overlap(a,b)
 return a[1]<=b[3]and a[3]>=b[1]and a[2]<=b[4]and a[4]>=b[2]
end
function Collision.hurt(a)
 local p=Collision.profiles[a.role];local height=a.crouch and p.crouch or p.height
 if a.down>0 then height=38 end
 return Collision.world(a,-p.width,0,p.width,height)
end
function Collision.attack(a,s,range)
 local roleMoves=Collision.moves[a.role];local override=roleMoves and roleMoves[a.attack.kind]
 if override then return Collision.world(a,override[1],override[2],override[3],override[4])end
 -- The travelling firebird owns a box at its current simulation position.
 -- Decorative trails do not turn the space behind it into a beam hitbox.
 if a.role==2 and a.attack.kind=='super'then
  local center=95+math.max(0,a.attack.t-a.attack.startup)*14
  return Collision.world(a,center-78,10,center+78,128)
 end
 local bottom,top=42,142
 if s.height=='low'then bottom,top=0,66
 elseif s.height=='high'then bottom,top=90,174
 elseif a.attack.kind=='rising'then bottom,top=20,s.heightRange or 200
 elseif a.attack.kind=='super'then bottom,top=12,s.heightRange or 190 end
 return Collision.world(a,8,bottom,range,top)
end
function Collision.push(a,b)
 if a.down>0 or b.down>0 then return end
 local pa,pb=Collision.profiles[a.role],Collision.profiles[b.role]
 local aa={a.x-pa.push,a.y,a.x+pa.push,a.y+pa.height}
 local bb={b.x-pb.push,b.y,b.x+pb.push,b.y+pb.height}
 if not Collision.overlap(aa,bb)then return end
 local direction=b.x>=a.x and 1 or -1;local penetration=pa.push+pb.push-math.abs(b.x-a.x)
 local ax,bx=a.x,b.x
 a.x=clamp(ax-direction*penetration/2,-535,535);b.x=clamp(bx+direction*penetration/2,-535,535)
 local remaining=pa.push+pb.push-math.abs(b.x-a.x)
 if remaining>0 then
  if a.x==-535 or a.x==535 then b.x=clamp(b.x+direction*remaining,-535,535)
  elseif b.x==-535 or b.x==535 then a.x=clamp(a.x-direction*remaining,-535,535)end
 end
end
