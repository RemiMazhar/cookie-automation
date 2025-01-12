import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from cali import Calibrator
from customsort import cmpCookies, mergesort

CAL_SIZE = 90 # longueur du trait de calibration (pour moi le bord de la table) en cm
THRESHOLD = 0.18 # écart minimum avec la couleur de la table pour qu'un pixel soit considéré cookiesque
TABLE_COLOR_HSV = (0, 0, 0.7) # on compare toutes les couleurs en HSV pcq H et S dépendent assez peu de l'éclairage

WEIGHTS = (0, 1, 0) # poids donnés aux composantes H S et V, 010 marche bien pour du blanc, à trouver par tatonnement pour d'autres couleurs
MIN_D, MAX_D = 3, 15 # diamètre minimum et maximum d'une composante connexe de pixels cookiesques pour qu'elle soit détectée comme un cookie

# calcule une différence de hue (chiant pcq modulo 180)
def dst_h(h1, h2):
    return np.minimum(abs(h1-h2), abs(h1-h2-180))

# crée un masque qui sélectionne les pixels cookiesques (=pas de la couleur de la table)
# retourne aussi une image "dst" représentant l'écart à la couleur de la table pour visualiser le processus
def make_mask(img):
    hsvimg = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(int)
    h,s,v = hsvimg[:,:,0],hsvimg[:,:,1],hsvimg[:,:,2]

    # on calcule séparément la différence de H, de S, et de V (normalisée entre 0 et 1)
    # puis on fait une moyenne quadratique pondérée des différences
    ch, cs, cv = WEIGHTS
    dh = dst_h(h, TABLE_COLOR_HSV[0])/90 # H defini modulo 180 donc la diff est entre 0 et 90
    ds = (s - TABLE_COLOR_HSV[1])/255
    dv = (v - TABLE_COLOR_HSV[2])/255
    dst = np.sqrt((ch * dh**2 + cs * ds**2 + cv * dv**2))

    mask = gaussian_filter(dst, sigma=1) >= THRESHOLD # flouté pcq ça marche mieux

    return (dst * 255).astype(np.uint8), (mask * 255).astype(np.uint8)



img = cv2.imread('cookies.jpg')
if img.shape[1] < img.shape[0] : img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) # format paysage pcq j'ai décidé
img = cv2.resize(img, (800, 600))

c = Calibrator()
zone, scale = c.get_zone(img, CAL_SIZE)
zone = np.array([zone])
print('échelle:', 1/scale, 'px/cm')

dst, mask = make_mask(img)
contours,hierarchy = cv2.findContours(mask, cv2.RETR_LIST, 2)
mask = np.stack((mask,)*3, -1)
dst = np.stack((dst,)*3, -1)

cookies_contours = []
diams = []
ctrs = []
for cnt in contours:
    d = 2 * np.sqrt(cv2.contourArea(cnt) / np.pi) * scale
    M = cv2.moments(cnt)
    if M["m00"] !=0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        if MIN_D <= d <= MAX_D and cv2.pointPolygonTest(zone, (cX, cY), False)==1:
            cookies_contours.append(cnt)
            diams.append(d)
            ctrs.append((cX, cY))

cookies = list(zip(ctrs, diams))
cookies = mergesort(cookies, cmpCookies)

img = cv2.drawContours(img, cookies_contours, -1, (0,255,0), 3)
img = cv2.drawContours(img, [zone], -1, (0, 0, 255), 3)
font                   = cv2.FONT_HERSHEY_SIMPLEX
fontScale              = 0.3
fontColor              = (255,255,255)
thickness              = 1
lineType               = 2
for i, ((cx, cy), d) in enumerate(cookies):
    img = cv2.putText(img, str(i), 
    (cx, cy), 
    font, 
    fontScale,
    fontColor,
    thickness,
    lineType)
cv2.imwrite('resdst.png', dst)
cv2.imwrite('resmask.png', mask)
cv2.imwrite('res.png', img)

with open('diameters.csv', 'w') as f:
    avg_diam = np.average(diams)
    std_diams = np.std(diams)
    f.write(
        'numéro, diamètre (cm), diamètre moyen (cm), écart-type (cm)\n'
        + '0, %i, %.2f, %.2f\n' % (cookies[0][1], avg_diam, std_diams)
        + '\n'.join(['%i,%.2f' % (i+1, d) for i,(ctr,d) in enumerate(cookies[1:])]))


plt.hist(diams, bins=15)
plt.xlabel('Diamètre (cm)')
plt.ylabel('Fréquence')
plt.savefig('histogram.png')

print('done (hopefully)')