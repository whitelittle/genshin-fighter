__loaders['gf_paint'] = function()
local G = require('gf_gfx')
local U = require('gf_util')

local P = {}
P.__index = P

local list = require('gf_bglist')
P.available = {}
for _, k in ipairs(list) do P.available[k] = true end

function P.new(parent, key, part, limit)
    local self=setmetatable({key=key,nodes={},jobs={},i=0,done=false,w=1600,h=900},P)
    self.group=G.group(parent)
    self.data={name='简约训练场',sub='轻量图元拼合'}
    local function add(shape,x,y,w,h,col)
        self.jobs[#self.jobs+1]={shape,x,y,w,h,col}
    end
    if part=='ground' then
        add(G.RECT,0,-220,6000,440,{89,98,94})
        add(G.RECT,0,-40,6000,80,{135,146,131})
        add(G.RECT,0,3,6000,6,{191,200,170})
    else
        add(G.RECT,0,0,6000,2400,{53,76,105})
        add(G.RECT,0,-120,6000,1000,{112,159,170})
        add(G.ELLIPSE,700,320,180,180,{242,229,184})
        for i=1,4 do add(G.ELLIPSE,-1500+i*700,300+(i%2)*90,480,85,{197,218,222}) end
        for i=-2,2 do add(G.TRI,i*950,-130,1500,800,{72,110,122}) end
        add(G.ELLIPSE,-1100,-320,3000,540,{65,119,90})
        add(G.ELLIPSE,1300,-350,3200,480,{76,135,99})
        for _,x in ipairs({-1200,1200}) do
            add(G.RECT,x,-130,70,420,{86,73,55})
            add(G.ELLIPSE,x,110,500,290,{64,114,77})
            add(G.ELLIPSE,x-130,65,320,220,{81,137,88})
        end
        add(G.RECT,0,-650,6000,450,{93,104,96})
        add(G.RECT,0,-415,6000,24,{183,197,162})
    end
    self.n=#self.jobs
    return self
end

function P:step(budget)
    if self.done then return true end
    local stop=math.min(self.n,self.i+budget)
    for i=self.i+1,stop do
        local s=self.jobs[i];local c=s[6]
        local node=G.image(self.group,s[1])
        node:pos(s[2],s[3]):size(s[4],s[5]):color(c[1],c[2],c[3],255):on(true)
        self.nodes[#self.nodes+1]=node
    end
    self.i=stop;self.done=stop==self.n
    return self.done
end

function P:free(later)
    if later then
        self.group:on(false)
        G.releaseLater(self.group)
        for _, n in ipairs(self.nodes) do G.releaseLater(n) end
        self.nodes = {}
        return
    end
    for _, n in ipairs(self.nodes) do G.release(n) end
    self.nodes = {}
    G.release(self.group)
end

return P
end
