# algo pour numéroter les cookies en sens de lecture
# enfin à peu près, pcq on en trouve jamais 2 exactement à la même ordonnée
# donc ya des histoires d'approximations
# bref c'est une relation d'ordre bricolée pour rendre la numérotation à peu près lisible
BIBLICALLY_ACCURATE_COOKIE_SPACING = 30

def cmpZ2(coords1: tuple[float, float], coords2: tuple[float, float]) -> bool:
    global BIBLICALLY_ACCURATE_COOKIE_SPACING
    x1, y1 = coords1
    x2, y2 = coords2
    if abs(y1 - y2) <= BIBLICALLY_ACCURATE_COOKIE_SPACING:
        return x1 < x2
    else:
        return y1 < y2
    
def cmpCookies(cookie1: tuple, cookie2: tuple) -> bool:
    coords1, d1, _ = cookie1
    coords2, d2, _ = cookie2
    return cmpZ2(coords1, coords2)