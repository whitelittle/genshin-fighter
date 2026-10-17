-- Move sets. Frame data at 60 Hz; distances in design units (1600 x 900 canvas, adult idle ~335 tall).
--
-- A move: pose (art pose shown), startup / active / recovery frames, damage (of 1000 hp),
-- hitstun / blockstun, push (knockback speed units/frame), launch (vertical speed on hit, juggles),
-- box = hitbox {x = front offset, y = bottom, w, h} relative to the fighter (x mirrored by facing),
-- level: 'mid' | 'low' | 'high' (high = must block standing, i.e. overheads / air attacks),
-- cancel: list of move ids it can cancel into on hit / block, energy: element energy gained on hit.
-- Presentation hints: fx (slash arc style), lunge (units moved forward during startup), tilt (degrees).
--
-- Weapon classes give the normals; each character adds a signature skill (E) and burst (Q).
local K = {}

local function m(t) t.recovery = t.recovery or 10 return t end

K.weapons = {
    sword = {
        reach = 1.0,
        light1 = m{pose = 'slash', startup = 5, active = 3, recovery = 9, damage = 32, hitstun = 15, blockstun = 11, push = 7,
                   box = {x = 40, y = 120, w = 150, h = 110}, cancel = {'light2', 'heavy', 'skill', 'burst'}, fx = 'arc', tilt = -6, lunge = 18, energy = 4},
        light2 = m{pose = 'slash', startup = 5, active = 3, recovery = 11, damage = 36, hitstun = 16, blockstun = 12, push = 8,
                   box = {x = 40, y = 100, w = 160, h = 120}, cancel = {'light3', 'heavy', 'skill', 'burst'}, fx = 'arcLow', tilt = 6, lunge = 24, energy = 4},
        light3 = m{pose = 'special', startup = 7, active = 4, recovery = 16, damage = 48, hitstun = 20, blockstun = 14, push = 12,
                   box = {x = 30, y = 80, w = 180, h = 150}, cancel = {'heavy', 'skill', 'burst'}, fx = 'thrust', lunge = 40, energy = 6},
        crouchLight = m{pose = 'crouch', startup = 5, active = 3, recovery = 9, damage = 26, hitstun = 14, blockstun = 10, push = 7,
                   box = {x = 40, y = 0, w = 150, h = 70}, level = 'low', cancel = {'crouchLight', 'crouchHeavy', 'skill', 'burst'}, fx = 'sweepLow', lunge = 16, energy = 3},
        heavy = m{pose = 'slash', windup = 'guard', startup = 10, active = 4, recovery = 18, damage = 70, hitstun = 22, blockstun = 16, push = 10,
                  launch = 22, box = {x = 30, y = 110, w = 190, h = 180}, cancel = {'skill', 'burst'}, fx = 'rise', tilt = -14, lunge = 30, energy = 8, shake = 6},
        crouchHeavy = m{pose = 'crouch', startup = 9, active = 4, recovery = 22, damage = 60, hitstun = 26, blockstun = 15, push = 6,
                  knockdown = true, box = {x = 40, y = 0, w = 200, h = 70}, level = 'low', cancel = {'skill', 'burst'}, fx = 'sweep', lunge = 30, energy = 8, tilt = 8},
        airLight = m{pose = 'jump', startup = 5, active = 6, recovery = 8, damage = 34, hitstun = 15, blockstun = 11, push = 6,
                  box = {x = 30, y = -40, w = 150, h = 140}, level = 'high', cancel = {'airHeavy', 'skill'}, fx = 'arc', tilt = -10, energy = 4},
        airHeavy = m{pose = 'slash', startup = 8, active = 6, recovery = 12, damage = 58, hitstun = 20, blockstun = 15, push = 8,
                  spike = 14, box = {x = 20, y = -80, w = 180, h = 170}, level = 'high', cancel = {'skill'}, fx = 'fall', tilt = 18, energy = 6, shake = 4},
    },
    claymore = {
        reach = 1.15, armorHeavy = true,
        light1 = m{pose = 'slash', startup = 7, active = 4, recovery = 12, damage = 42, hitstun = 17, blockstun = 12, push = 9,
                   box = {x = 40, y = 110, w = 175, h = 130}, cancel = {'light2', 'heavy', 'skill', 'burst'}, fx = 'arcHeavy', tilt = -8, lunge = 16, energy = 4, shake = 2},
        light2 = m{pose = 'special', startup = 8, active = 4, recovery = 16, damage = 52, hitstun = 19, blockstun = 13, push = 11,
                   box = {x = 40, y = 90, w = 190, h = 150}, cancel = {'heavy', 'skill', 'burst'}, fx = 'arcLowHeavy', tilt = 8, lunge = 26, energy = 5, shake = 3},
        crouchLight = m{pose = 'crouch', startup = 7, active = 3, recovery = 12, damage = 34, hitstun = 15, blockstun = 11, push = 8,
                   box = {x = 40, y = 0, w = 170, h = 75}, level = 'low', cancel = {'crouchHeavy', 'skill', 'burst'}, fx = 'sweepLow', lunge = 16, energy = 3},
        heavy = m{pose = 'slash', windup = 'guard', startup = 15, active = 5, recovery = 22, damage = 105, hitstun = 26, blockstun = 19, push = 14,
                  launch = 24, armor = true, box = {x = 30, y = 90, w = 230, h = 220}, cancel = {'skill', 'burst'}, fx = 'smash', tilt = -18, lunge = 34, energy = 10, shake = 10},
        crouchHeavy = m{pose = 'crouch', startup = 12, active = 5, recovery = 26, damage = 80, hitstun = 28, blockstun = 17, push = 7,
                  knockdown = true, box = {x = 40, y = 0, w = 235, h = 80}, level = 'low', cancel = {'skill', 'burst'}, fx = 'sweep', lunge = 34, energy = 9, tilt = 8, shake = 4},
        airLight = m{pose = 'jump', startup = 7, active = 6, recovery = 10, damage = 44, hitstun = 16, blockstun = 12, push = 7,
                  box = {x = 30, y = -40, w = 170, h = 150}, level = 'high', cancel = {'airHeavy', 'skill'}, fx = 'arcHeavy', tilt = -10, energy = 4},
        airHeavy = m{pose = 'slash', startup = 11, active = 7, recovery = 14, damage = 78, hitstun = 22, blockstun = 16, push = 9,
                  spike = 18, box = {x = 10, y = -100, w = 200, h = 190}, level = 'high', cancel = {'skill'}, fx = 'fallHeavy', tilt = 24, energy = 6, shake = 7},
    },
    polearm = {
        reach = 1.2,
        light1 = m{pose = 'slash', startup = 6, active = 3, recovery = 10, damage = 34, hitstun = 15, blockstun = 11, push = 8,
                   box = {x = 50, y = 140, w = 200, h = 70}, cancel = {'light2', 'heavy', 'skill', 'burst'}, fx = 'thrust', lunge = 20, energy = 4},
        light2 = m{pose = 'slash', startup = 6, active = 3, recovery = 12, damage = 38, hitstun = 16, blockstun = 12, push = 9,
                   box = {x = 40, y = 100, w = 215, h = 110}, cancel = {'light3', 'heavy', 'skill', 'burst'}, fx = 'arc', tilt = -8, lunge = 22, energy = 4},
        light3 = m{pose = 'special', startup = 8, active = 5, recovery = 16, damage = 50, hitstun = 20, blockstun = 14, push = 12,
                   box = {x = 30, y = 70, w = 230, h = 170}, cancel = {'heavy', 'skill', 'burst'}, fx = 'spin', lunge = 36, energy = 6},
        crouchLight = m{pose = 'crouch', startup = 6, active = 3, recovery = 10, damage = 28, hitstun = 14, blockstun = 10, push = 7,
                   box = {x = 50, y = 0, w = 200, h = 65}, level = 'low', cancel = {'crouchLight', 'crouchHeavy', 'skill', 'burst'}, fx = 'thrustLow', lunge = 16, energy = 3},
        heavy = m{pose = 'slash', windup = 'guard', startup = 11, active = 4, recovery = 19, damage = 74, hitstun = 22, blockstun = 16, push = 11,
                  launch = 23, box = {x = 30, y = 110, w = 230, h = 200}, cancel = {'skill', 'burst'}, fx = 'rise', tilt = -16, lunge = 30, energy = 8, shake = 6},
        crouchHeavy = m{pose = 'crouch', startup = 10, active = 4, recovery = 23, damage = 62, hitstun = 26, blockstun = 15, push = 6,
                  knockdown = true, box = {x = 50, y = 0, w = 240, h = 70}, level = 'low', cancel = {'skill', 'burst'}, fx = 'sweep', lunge = 30, energy = 8, tilt = 6},
        airLight = m{pose = 'jump', startup = 6, active = 6, recovery = 8, damage = 34, hitstun = 15, blockstun = 11, push = 6,
                  box = {x = 40, y = -50, w = 180, h = 120}, level = 'high', cancel = {'airHeavy', 'skill'}, fx = 'thrust', tilt = -20, energy = 4},
        airHeavy = m{pose = 'slash', startup = 9, active = 6, recovery = 12, damage = 60, hitstun = 20, blockstun = 15, push = 8,
                  spike = 15, box = {x = 20, y = -110, w = 190, h = 190}, level = 'high', cancel = {'skill'}, fx = 'fall', tilt = 30, energy = 6, shake = 4},
    },
    catalyst = {
        reach = 0.95, ranged = true,
        light1 = m{pose = 'slash', startup = 6, active = 3, recovery = 10, damage = 30, hitstun = 15, blockstun = 11, push = 8,
                   box = {x = 60, y = 120, w = 150, h = 120}, cancel = {'light2', 'heavy', 'skill', 'burst'}, fx = 'burstSmall', lunge = 12, energy = 5},
        light2 = m{pose = 'special', startup = 7, active = 4, recovery = 14, damage = 42, hitstun = 18, blockstun = 12, push = 10,
                   box = {x = 70, y = 90, w = 170, h = 150}, cancel = {'heavy', 'skill', 'burst'}, fx = 'burst', lunge = 14, energy = 5},
        crouchLight = m{pose = 'crouch', startup = 6, active = 3, recovery = 10, damage = 26, hitstun = 14, blockstun = 10, push = 7,
                   box = {x = 50, y = 0, w = 150, h = 70}, level = 'low', cancel = {'crouchLight', 'crouchHeavy', 'skill', 'burst'}, fx = 'burstLow', lunge = 10, energy = 3},
        heavy = m{pose = 'special', windup = 'guard', startup = 14, active = 3, recovery = 18, damage = 60, hitstun = 22, blockstun = 15, push = 10,
                  projectile = {speed = 15, w = 90, h = 80, y = 150, life = 70, style = 'orb'}, cancel = {'skill', 'burst'}, energy = 8},
        crouchHeavy = m{pose = 'crouch', startup = 10, active = 5, recovery = 24, damage = 58, hitstun = 26, blockstun = 15, push = 6,
                  knockdown = true, box = {x = 40, y = 0, w = 210, h = 80}, level = 'low', cancel = {'skill', 'burst'}, fx = 'burstLow', lunge = 22, energy = 8},
        airLight = m{pose = 'jump', startup = 6, active = 6, recovery = 9, damage = 32, hitstun = 15, blockstun = 11, push = 6,
                  box = {x = 40, y = -40, w = 150, h = 140}, level = 'high', cancel = {'airHeavy', 'skill'}, fx = 'burstSmall', energy = 4},
        airHeavy = m{pose = 'special', startup = 10, active = 3, recovery = 14, damage = 50, hitstun = 20, blockstun = 14, push = 8,
                  projectile = {speed = 14, vy = -8, w = 80, h = 80, y = 60, life = 60, style = 'orb'}, level = 'high', cancel = {'skill'}, energy = 6},
    },
    bow = {
        reach = 0.95, ranged = true,
        light1 = m{pose = 'slash', startup = 5, active = 3, recovery = 9, damage = 30, hitstun = 15, blockstun = 11, push = 8,
                   box = {x = 40, y = 120, w = 140, h = 110}, cancel = {'light2', 'heavy', 'skill', 'burst'}, fx = 'arc', tilt = -6, lunge = 14, energy = 4},
        light2 = m{pose = 'special', startup = 6, active = 4, recovery = 12, damage = 38, hitstun = 17, blockstun = 12, push = 9,
                   box = {x = 40, y = 90, w = 160, h = 140}, cancel = {'heavy', 'skill', 'burst'}, fx = 'kick', lunge = 22, energy = 4},
        crouchLight = m{pose = 'crouch', startup = 5, active = 3, recovery = 9, damage = 24, hitstun = 14, blockstun = 10, push = 7,
                   box = {x = 40, y = 0, w = 140, h = 70}, level = 'low', cancel = {'crouchLight', 'crouchHeavy', 'skill', 'burst'}, fx = 'sweepLow', lunge = 12, energy = 3},
        heavy = m{pose = 'special', windup = 'guard', startup = 13, active = 3, recovery = 17, damage = 56, hitstun = 22, blockstun = 15, push = 10,
                  projectile = {speed = 26, w = 120, h = 30, y = 175, life = 60, style = 'arrow'}, cancel = {'skill', 'burst'}, energy = 8},
        crouchHeavy = m{pose = 'crouch', startup = 9, active = 4, recovery = 22, damage = 56, hitstun = 26, blockstun = 15, push = 6,
                  knockdown = true, box = {x = 40, y = 0, w = 200, h = 75}, level = 'low', cancel = {'skill', 'burst'}, fx = 'sweep', lunge = 24, energy = 8},
        airLight = m{pose = 'jump', startup = 5, active = 6, recovery = 8, damage = 30, hitstun = 15, blockstun = 11, push = 6,
                  box = {x = 30, y = -40, w = 140, h = 140}, level = 'high', cancel = {'airHeavy', 'skill'}, fx = 'kick', energy = 4},
        airHeavy = m{pose = 'special', startup = 9, active = 3, recovery = 12, damage = 46, hitstun = 20, blockstun = 14, push = 8,
                  projectile = {speed = 24, vy = -12, w = 110, h = 30, y = 60, life = 50, style = 'arrow'}, level = 'high', cancel = {'skill'}, energy = 6},
    },
}

-- Throw (all characters): close range, unblockable, beats guard, loses to attacks.
K.throw = {pose = 'slash', startup = 4, active = 2, recovery = 26, damage = 90, range = 130, knockdown = true, energy = 10}

-- Signature skills (E). style: projectile | rush | rising | zone | pillar
-- cd: cooldown frames. coat: frames the caster is coated with its element (reaction window).
K.skills = {
    raidenshogun  = {style = 'zone',  startup = 12, recovery = 18, damage = 80, cd = 150, delay = 18, w = 170, h = 260, fx = 'eye', hitstun = 28, launch = 16},
    furina        = {style = 'projectile', startup = 13, recovery = 16, damage = 70, cd = 140, speed = 13, w = 110, h = 110, y = 140, life = 90, fx = 'bubble', hitstun = 24},
    zhongli       = {style = 'pillar', startup = 14, recovery = 18, damage = 85, cd = 160, dist = 200, w = 120, h = 320, fx = 'pillar', hitstun = 28, launch = 24, shield = 120},
    mavuika       = {style = 'rush', startup = 10, recovery = 16, damage = 90, cd = 150, speed = 34, dur = 16, w = 170, h = 220, fx = 'flameRush', hitstun = 26, launch = 18, armor = true},
    nahida        = {style = 'zone',  startup = 12, recovery = 16, damage = 70, cd = 140, delay = 14, w = 200, h = 220, fx = 'seed', hitstun = 30, snare = 40},
    venti         = {style = 'rising', startup = 6, recovery = 22, damage = 75, cd = 150, w = 210, h = 340, fx = 'wind', hitstun = 30, launch = 30, invuln = 8},
    kamisatoayaka = {style = 'rising', startup = 7, recovery = 20, damage = 85, cd = 150, w = 260, h = 260, fx = 'iceBloom', hitstun = 28, launch = 26, invuln = 6},
    tartaglia     = {style = 'rush', startup = 9, recovery = 14, damage = 80, cd = 140, speed = 30, dur = 14, w = 170, h = 220, fx = 'hydroRush', hitstun = 24, hits = 3},
    aratakiitto   = {style = 'projectile', startup = 14, recovery = 18, damage = 95, cd = 170, speed = 16, w = 130, h = 150, y = 70, life = 80, fx = 'ushi', hitstun = 30, knockdown = true},
    yaemiko       = {style = 'zone',  startup = 11, recovery = 15, damage = 75, cd = 140, delay = 22, w = 140, h = 360, fx = 'sakura', hitstun = 28, launch = 20},
    arlecchino    = {style = 'rush', startup = 10, recovery = 16, damage = 88, cd = 150, speed = 32, dur = 15, w = 180, h = 220, fx = 'bloodRush', hitstun = 26, launch = 16},
    wanderer      = {style = 'rising', startup = 6, recovery = 20, damage = 70, cd = 140, w = 200, h = 300, fx = 'wind', hitstun = 28, launch = 30, invuln = 8},
    neuvillette   = {style = 'projectile', startup = 16, recovery = 18, damage = 80, cd = 150, speed = 20, w = 260, h = 90, y = 150, life = 70, fx = 'torrent', hitstun = 26},
    clorinde      = {style = 'rush', startup = 8, recovery = 14, damage = 82, cd = 140, speed = 36, dur = 12, w = 170, h = 220, fx = 'nightRush', hitstun = 24},
    navia         = {style = 'projectile', startup = 12, recovery = 20, damage = 100, cd = 170, speed = 22, w = 200, h = 200, y = 120, life = 18, fx = 'shards', hitstun = 30, knockdown = true},
    skirk         = {style = 'rush', startup = 7, recovery = 14, damage = 84, cd = 140, speed = 40, dur = 11, w = 170, h = 220, fx = 'voidRush', hitstun = 24, invuln = 6},
}

-- Bursts (Q): cost 100 energy. style: beam | aoe | rush | rain.
K.bursts = {
    raidenshogun  = {style = 'aoe',  damage = 300, hits = 3, range = 900, fx = 'musou'},
    furina        = {style = 'aoe',  damage = 260, hits = 4, range = 1000, fx = 'fanfare'},
    zhongli       = {style = 'rain', damage = 280, hits = 1, range = 2400, fx = 'meteor', petrify = 70},
    mavuika       = {style = 'rush', damage = 320, hits = 4, range = 700, fx = 'sunfell'},
    nahida        = {style = 'aoe',  damage = 250, hits = 3, range = 2400, fx = 'shrine'},
    venti         = {style = 'aoe',  damage = 260, hits = 6, range = 700, fx = 'stormeye', pull = true},
    kamisatoayaka = {style = 'beam', damage = 290, hits = 6, range = 1100, fx = 'soumetsu'},
    tartaglia     = {style = 'rush', damage = 310, hits = 3, range = 600, fx = 'havoc'},
    aratakiitto   = {style = 'rush', damage = 330, hits = 4, range = 520, fx = 'oni'},
    yaemiko       = {style = 'rain', damage = 290, hits = 4, range = 2400, fx = 'tenko'},
    arlecchino    = {style = 'rush', damage = 320, hits = 3, range = 650, fx = 'balemoon'},
    wanderer      = {style = 'aoe',  damage = 270, hits = 5, range = 800, fx = 'kyougen'},
    neuvillette   = {style = 'beam', damage = 300, hits = 3, range = 2400, fx = 'tides'},
    clorinde      = {style = 'rush', damage = 300, hits = 5, range = 700, fx = 'lastlight'},
    navia         = {style = 'rain', damage = 300, hits = 4, range = 1200, fx = 'salvo'},
    skirk         = {style = 'beam', damage = 310, hits = 5, range = 900, fx = 'havocRuin'},
}

-- Per-character body stats (speed in units/frame, health of 1000 scale)
K.body = {
    default = {walk = 4.4, back = 3.6, dash = 13, health = 1000, weight = 1.0},
    aratakiitto = {walk = 3.9, back = 3.2, dash = 12, health = 1080, weight = 1.15},
    navia = {walk = 4.0, back = 3.3, dash = 12, health = 1050, weight = 1.1},
    mavuika = {walk = 4.1, back = 3.4, dash = 12.5, health = 1040, weight = 1.1},
    zhongli = {walk = 4.0, back = 3.4, dash = 12, health = 1060, weight = 1.1},
    nahida = {walk = 4.8, back = 4.0, dash = 14, health = 950, weight = 0.9},
    venti = {walk = 4.7, back = 3.9, dash = 14, health = 960, weight = 0.92},
    skirk = {walk = 4.8, back = 3.8, dash = 15, health = 970, weight = 0.95},
    clorinde = {walk = 4.7, back = 3.8, dash = 14.5, health = 980, weight = 0.97},
}

-- Elemental reactions: K.reaction[attacker][victim aura] -> reaction id
K.reactionName = {
    vaporize = '蒸发', melt = '融化', overload = '超载', frozen = '冻结', electro = '感电', superconduct = '超导',
    swirl = '扩散', crystal = '结晶', bloom = '绽放', aggravate = '激化', burning = '燃烧',
}
local R = {}
local function pair(a, b, r) R[a] = R[a] or {}; R[b] = R[b] or {}; R[a][b] = r; R[b][a] = r end
pair('hydro', 'pyro', 'vaporize')
pair('cryo', 'pyro', 'melt')
pair('electro', 'pyro', 'overload')
pair('hydro', 'cryo', 'frozen')
pair('electro', 'hydro', 'electro')
pair('electro', 'cryo', 'superconduct')
pair('dendro', 'hydro', 'bloom')
pair('dendro', 'electro', 'aggravate')
pair('dendro', 'pyro', 'burning')
for _, e in ipairs({'hydro', 'pyro', 'electro', 'cryo'}) do
    R.anemo = R.anemo or {}; R.anemo[e] = 'swirl'; R[e].anemo = 'swirl'
    R.geo = R.geo or {}; R.geo[e] = 'crystal'; R[e].geo = 'crystal'
end
K.reaction = R

K.elementColor = {
    anemo = {116, 255, 214}, geo = {255, 200, 64}, electro = {196, 120, 255}, dendro = {150, 230, 60},
    hydro = {60, 170, 255}, pyro = {255, 110, 50}, cryo = {160, 230, 255},
}
K.elementName = {anemo = '风', geo = '岩', electro = '雷', dendro = '草', hydro = '水', pyro = '火', cryo = '冰'}
K.weaponName = {sword = '单手剑', claymore = '双手剑', polearm = '长柄武器', catalyst = '法器', bow = '弓'}

K.en = {
    raidenshogun = 'RAIDEN SHOGUN', furina = 'FURINA', zhongli = 'ZHONGLI', mavuika = 'MAVUIKA', nahida = 'NAHIDA',
    venti = 'VENTI', kamisatoayaka = 'KAMISATO AYAKA', tartaglia = 'TARTAGLIA', aratakiitto = 'ARATAKI ITTO',
    yaemiko = 'YAE MIKO', arlecchino = 'ARLECCHINO', wanderer = 'WANDERER', neuvillette = 'NEUVILLETTE',
    clorinde = 'CLORINDE', navia = 'NAVIA', skirk = 'SKIRK',
}
K.title = {
    raidenshogun = '永恒的雷光', furina = '不休的独舞', zhongli = '尘世闲游', mavuika = '燃烧的太阳', nahida = '白草净华',
    venti = '风色诗人', kamisatoayaka = '白鹭霜华', tartaglia = '公子', aratakiitto = '花坂豪快', yaemiko = '浮世笑百姿',
    arlecchino = '「仆人」', wanderer = '久世浮倾', neuvillette = '谕告的潮音', clorinde = '秉烛狝影', navia = '明花蔓舵',
    skirk = '深渊的剑客',
}

return K
