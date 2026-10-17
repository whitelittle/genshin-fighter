__loaders['gf_sim_flow']=function()
local floor,abs,max,min=math.floor,math.abs,math.max,math.min
return function(S,C)
function S:roundOver(winner, reason)
    self.phase = 'ko'
    self.phaseT = 0
    self.koReason = reason
    self.roundWinner = winner
    if winner then self.f[winner].wins = self.f[winner].wins + 1 end
    self:emit({type = 'roundEnd', winner = winner, reason = reason,
               perfect = winner and self.f[winner].hp == self.f[winner].maxhp})
end

function S:flow()
    self.phaseT = self.phaseT + 1
    local a, b = self.f[1], self.f[2]
    if self.phase == 'intro' then
        if self.phaseT == 1 then self:emit({type = 'announce', what = 'round', round = self.round}) end
        if self.phaseT == 40 then self:emit({type='announce',what='fight'}) end
        if self.phaseT >= 60 then
            self.phase = 'fight'
            self.phaseT = 0
            for _, p in ipairs(self.f) do self:setState(p, 'idle') end
        end
    elseif self.phase == 'fight' then
        if not self.opts.training and self.timeLimit < 999 then
            self.timer = self.timer - 1
            if self.timer % 60 == 0 then self:emit({type = 'second', left = self.timer // 60}) end
        else
            self.timer = self.timeLimit * 60
        end
        if self.opts.training then
            for _, p in ipairs(self.f) do
                if p.hp <= 0 then p.hp = p.maxhp; p.ko = false end
                if p.state == 'idle' and p.combo == 0 and p.hp < p.maxhp and p.t > 60 then p.hp = min(p.maxhp, p.hp + 20) end
                if self.opts.infinite then p.energy = 100 end
            end
            return
        end
        local ka, kb = a.hp <= 0, b.hp <= 0
        if ka or kb then
            local w
            if not (ka and kb) then w = ka and 2 or 1 end   -- double K.O.: nobody wins the round
            self:roundOver(w, (ka and kb) and 'double' or 'ko')
        elseif self.timer <= 0 then
            local w
            if a.hp * b.maxhp > b.hp * a.maxhp then w = 1 elseif b.hp * a.maxhp > a.hp * b.maxhp then w = 2 end
            self:roundOver(w, 'time')
        end
    elseif self.phase == 'ko' then
        -- wait for the loser to land, then victory pose
        if self.phaseT == 150 then
            local w = self.roundWinner
            for _, p in ipairs(self.f) do
                if w and p.id == w and p.state ~= 'airhit' and p.state ~= 'down' then self:setState(p, 'win'); p.vx = 0 end
            end
            self:emit({type = 'victoryPose', p = w})
        end
        if self.phaseT >= 260 then
            local w = self.roundWinner
            if (w and self.f[w].wins >= self.winsNeeded) or self.round >= 9 then
                -- round cap (draws): the side with more round wins takes the match
                if not (w and self.f[w].wins >= self.winsNeeded) then
                    local wa, wb = self.f[1].wins, self.f[2].wins
                    w = wa > wb and 1 or (wb > wa and 2 or nil)
                end
                self.phase = 'over'
                self.phaseT = 0
                self.matchWinner = w
                self:emit({type = 'matchEnd', winner = w})
            else
                self.round = self.round + 1
                self:startRound(false)
            end
        end
    end
end


end
end
