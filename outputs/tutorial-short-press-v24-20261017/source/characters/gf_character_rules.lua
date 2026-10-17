__loaders['gf_character_rules']=function()
return function(K)
K.skills = {
    raidenshogun  = {style = 'zone',  startup = 12, recovery = 18, damage = 80, cd = 150, delay = 18, w = 170, h = 260, fx = 'eye', hitstun = 28, launch = 16},
    furina        = {style = 'projectile', startup = 13, recovery = 16, damage = 70, cd = 140, speed = 13, w = 110, h = 110, y = 140, life = 90, fx = 'bubble', hitstun = 24},
    zhongli       = {style = 'pillar', startup = 14, recovery = 18, damage = 85, cd = 160, dist = 200, w = 120, h = 320, fx = 'pillar', hitstun = 28, launch = 24, shield = 120},
    mavuika       = {style = 'rush', startup = 10, recovery = 16, damage = 90, cd = 150, speed = 34, dur = 16, w = 170, h = 220, fx = 'flameRush', hitstun = 26, launch = 18, armor = true},
    nahida        = {style = 'capture', startup = 8, recovery = 22, damage = 70, cd = 140, range = 650, w = 280, h = 340, fx = 'capture', hitstun = 30},
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


end
end
