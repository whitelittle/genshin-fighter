-- Visual frame selection is derived from rollback simulation, never from image callbacks.
local function group1Sequence(seq,t)
 if not seq then return nil end
 for _,item in ipairs(seq)do if t<item[2]then return item[1]end;t=t-item[2]end
 return seq[#seq][1]
end
local function group1Pose(a,i)
 local m=group1Motion[a.role];if not m then return nil end
 local ids=poseIds[a.role]
 if phase~='fight' and phase~='intro' and phase~='roundLoad' and a.hp>0 and f[3-i].hp<=0 then return ids.attack14 end
 if a.down>0 then return ids.basic14
 elseif a.wake>0 then return ids.basic15
 elseif a.launched then return ids.basic13
 elseif a.stun>0 then return ids.basic12
 elseif a.attack then
  local atk=a.attack;local spec=specs[a.role][atk.kind];if not spec then return ids.basic0 end
  local kind=(atk.kind=='special'or atk.kind=='teleport'or atk.kind=='e2'or atk.kind=='e3')and'E'or atk.kind=='super'and'Q'or atk.kind=='low'and'lowA'or atk.kind=='rising'and'airA'or'A'
  if kind=='A'or kind=='E'then
   local offset=kind=='E'and 8 or 0;local t=atk.t;local phase,index
   if t<atk.startup then index=math.min(2,math.floor(t/math.max(1,atk.startup)*3))
   elseif t<atk.startup+spec.active then index=3+math.min(1,math.floor((t-atk.startup)/math.max(1,spec.active)*2))
   else index=5+math.min(2,math.floor((t-atk.startup-spec.active)/math.max(1,spec.recovery)*3))end
   return ids['connections'..(offset+index)]
  end
  local first=kind=='Q'and 11 or kind=='lowA'and 3 or 6
  local phase=atk.t<atk.startup and 0 or atk.t<atk.startup+spec.active and 1 or 2
  if kind=='airA'and phase==2 then return ids.basic10 end
  return ids['attack'..(first+phase)]or ids.basic10
 elseif a.y>0 then return ids[a.vy>0 and'basic9'or'basic10']
 elseif a.block then return ids[a.crouch and'basic7'or'basic6']
 elseif a.crouch then return ids.basic5
 elseif controls[i]and controls[i].input and(controls[i].input.left or controls[i].input.right)then return group1Sequence(m.walk,tick%32)
 end
 return group1Sequence(m.idle,tick%48)
end
