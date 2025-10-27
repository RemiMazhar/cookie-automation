from functools import cmp_to_key
import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares
from scipy.stats import linregress
from customsort import cmpCookies
from cali import Calibrator
from matplotlib import ticker

CAL_SIZE: float = 75 # longueur du trait de calibration (pour moi le bord de la table) en cm
THRESHOLD: float = 0.275 # écart minimum avec la couleur de la table pour qu'un pixel soit considéré cookiesque
TABLE_COLOR_HSV: tuple[float, float, float] = (0, 0, 0.7) # on compare toutes les couleurs en HSV pcq H et S dépendent assez peu de l'éclairage

WEIGHTS: tuple[float, float, float] = (0, 1, 0) # poids donnés aux composantes H S et V, 010 marche bien pour du blanc, à trouver par tatonnement pour d'autres couleurs
MIN_D, MAX_D = 3, 15 # diamètre minimum et maximum d'une composante connexe de pixels cookiesques pour qu'elle soit détectée comme un cookie

# calcule une différence de hue (chiant pcq modulo 180)
def dst_h(h1, h2):
    return np.minimum(abs(h1-h2), abs(h1-h2-180))

# crée un masque qui sélectionne les pixels cookiesques (=pas de la couleur de la table)
# retourne aussi une image "dst" représentant l'écart à la couleur de la table pour visualiser le processus
def make_mask(img):
    global THRESHOLD, TABLE_COLOR_HSV, WEIGHTS
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


def generate_diameters(diams: list, roundnesses: list, cookies: list, total_area: float) -> None:
    """génère un fichier diameters.csv avec les diamètres et rotondités des cookies détectés, ainsi que des statistiques diverses"""
    avg_diam = np.average(diams)
    std_diams = np.std(diams)
    total_mass = int(input("total mass:"))  
    avg_mass = total_mass / len(diams)
    qte = len(diams) / 6.02e23
    molar_mass = total_mass / qte
    mass_per_area = total_mass / total_area
    area_per_qte = total_area / qte
    avg_roundness = np.average(roundnesses)
    std_roundnesses = np.std(roundnesses)
    sch_rad = 2 * 6.67e-11 / 2.998e8**2 * total_mass / 1000
    molar_sch_rad = 2 * 6.67e-11 / 2.998e8**2 * molar_mass / 1000

    with open('diameters.csv', 'w') as f:
        lines = ['numéro,diamètre (cm),rotondité'] + ['%i,%.2f,%.2f' % (i, d, r) for i,(ctr,d,r) in enumerate(cookies)]
        if len(lines) < 14:
            lines += [',,' for _ in range(14 - len(lines))]
        lines[1] += ',diamètre moyen (cm),%.2f' % avg_diam
        lines[2] += ',écart-type du diamètre (cm),%.2f' % std_diams
        lines[3] += ',rotondité moyenne,%.2f' % avg_roundness
        lines[4] += ',écart-type de la rotondité,%.2f' % std_roundnesses
        lines[5] += ',masse totale (g),%.2f' % total_mass
        lines[6] += ',quantité totale (mol),{:.2e}'.format(qte)
        lines[7] += ',surface totale (cm²),%.2f' % total_area
        lines[8] += ',masse moyenne  d\'un cookie (g),%.2f' % avg_mass
        lines[9] += ',masse molaire (masse lunaire/mol),%.2f' % (molar_mass / 1000 / 8.1e22)
        lines[10] += ',masse surfacique (g/cm²),%.2f' % mass_per_area
        lines[11] += ',surface molaire (surface terrestre/mol),{:.2e}'.format(area_per_qte / 1e8 / 510e6)
        lines[12] += ',rayon de schwarschild (m),{:.2e}'.format(sch_rad)
        lines[13] += ',rayon de schwarschild molaire (µm/mol),%.2f' % (molar_sch_rad * 1e6)
        f.write('\n'.join(lines))

def main():
    global MIN_D, MAX_D, CAL_SIZE
    img = cv2.imread('cookies.jpg')
    if img.shape[1] < img.shape[0] : img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) # format paysage pcq j'ai décidé # AT: Bon ok
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
    roundnesses = []
    total_area = 0
    for cnt in contours:
        contour_area = cv2.contourArea(cnt)
        d = 2 * np.sqrt(contour_area / np.pi) * scale
        total_area += contour_area * scale**2
        M = cv2.moments(cnt)

        if M["m00"] !=0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            if MIN_D <= d <= MAX_D and cv2.pointPolygonTest(zone, (cX, cY), False)==1:
                cookies_contours.append(cnt)
                diams.append(d)
                ctrs.append((cX, cY))
            
                roundnesses.append(contour_area / (np.pi*cv2.minEnclosingCircle(cnt)[1]**2))
                #def sqdst(r):
                #    return sum((np.sqrt((x-cX)**2 + (y-cY)**2) - r)**2 for ((x,y),) in cnt)
                #roundnesses.append(max(0, 1 - np.sqrt(least_squares(sqdst, 0).cost) / len(cnt) / d))

    cookies = list(zip(ctrs, diams, roundnesses))
    cookies.sort(key=cmp_to_key(cmpCookies))

    img = cv2.drawContours(img, cookies_contours, -1, (0,255,0), 3)
    img = cv2.drawContours(img, [zone], -1, (0, 0, 255), 3)
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    fontScale              = 0.3
    fontColor              = (255,255,255)
    thickness              = 1
    lineType               = 2
    for i, ((cx, cy), d, r) in enumerate(cookies):
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

    generate_diameters(diams, roundnesses, cookies, total_area)

    plt.hist(diams, bins=15)
    plt.xlabel('Diamètre (cm)')
    plt.ylabel('Fréquence')
    plt.title('Distribution des diamètres')
    plt.savefig('diam_histogram.png')
    plt.close()

    plt.hist(roundnesses, bins=15)
    plt.xlabel('Rotondité')
    plt.ylabel('Fréquence')
    plt.title('Distribution des rotondités')
    plt.savefig('roundness_histogram.png')
    plt.close()

    plt.scatter(diams, roundnesses)
    regress = linregress(diams, np.log(np.array(roundnesses)))
    ys = np.exp(regress.intercept + regress.slope * np.array(diams))
    print(100 * regress.slope, '% par cm')
    lbl = ('+' if regress.slope >=0 else '') + ('%.1f %% de rotondité par cm' % (100 * regress.slope))
    plt.plot(diams, ys, color='orange', label=lbl)
    #plt.yscale('log')
    plt.xlabel('Diamètre (cm)')
    plt.ylabel('Rotondité')
    plt.title('Rotondité en fonction du diamètre')
    plt.legend()
    plt.savefig('roundness_diam_scatter.png')

    print('done (hopefully)')


if __name__ == "__main__":
    main()