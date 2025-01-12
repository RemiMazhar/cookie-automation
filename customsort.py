# algo pour numéroter les cookies en sens de lecture
# enfin à peu près, pcq on en trouve jamais 2 exactement à la même ordonnée
# donc ya des histoires d'approximations
# bref c'est une relation d'ordre bricolée pour rendre la numérotation à peu près lisible


def cmpZ2(coords1, coords2):
    x1, y1 = coords1
    x2, y2 = coords2
    if abs(y1 - y2) <= 30:
        return x1 < x2
    else:
        return y1 < y2
    
def cmpCookies(cookie1, cookie2):
    coords1, d1 = cookie1
    coords2, d2 = cookie2
    return cmpZ2(coords1, coords2)

def merge(l1, l2, compare):
    n = len(l1)
    m = len(l2)
    lres = [0]*(n+m)
    i1 = 0
    i2 = 0
    for i in range(n+m):
        if i2 >= m:
            lres[i] = l1[i1]
            i1 += 1
        elif i1 >= n:
            lres[i] = l2[i2]
            i2 += 1
        elif compare(l1[i1], l2[i2]):
            lres[i] = l1[i1]
            i1 += 1
        else:
            lres[i] = l2[i2]
            i2 += 1
    return lres

def mergesort(l, compare):
    n = len(l)
    if n <= 1: return l
    return merge(mergesort(l[:n//2], compare), mergesort(l[n//2:], compare), compare)