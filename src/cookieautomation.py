from functools import cmp_to_key
import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.stats import linregress
from customsort import cmpCookies
from cali import Calibrator
from os import path
from pathlib import Path
from optparse import OptionParser

# Path setup
CURR_DIR = path.dirname(path.abspath(__file__)).replace('\\', '/')
OUT_DIR = f"{CURR_DIR}/out"
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

CAL_SIZE: float = 90 # longueur du trait de calibration (pour moi le bord de la table) en cm
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
    global OUT_DIR
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

    with open(f'{OUT_DIR}/diameters.csv', 'w') as f:
        lines = ['numero,diametre (cm),rotondite'] + [f'{i},{d:.2f},{r:.2f}' for i,(ctr,d,r) in enumerate(cookies)]
        f.write('\n'.join(lines))

    with open(f'{OUT_DIR}/stats.csv', 'w') as f:
        lines = ""
        lines += f'diametre moyen (cm),{avg_diam:.2f}\n'
        lines += f'ecart-type du diametre (cm),{std_diams:.2f}\n'
        lines += f'rotondite moyenne,{avg_roundness:.2f}\n'
        lines += f'ecart-type de la rotondite,{std_roundnesses:.2f}\n'
        lines += f'masse totale (g),{total_mass:.2f}\n'
        lines += f'quantite totale (mol),{qte:.2e}\n'
        lines += f'surface totale (cm^2),{total_area:.2f}\n'
        lines += f'masse moyenne  d\'un cookie (g),{avg_mass:.2f}\n'
        lines += f'masse molaire (masse lunaire/mol),{molar_mass / 1000 / 8.1e22:.2f}\n'
        lines += f'masse surfacique (g/cm^2),{mass_per_area:.2f}\n'
        lines += f'surface molaire (surface terrestre/mol),{area_per_qte / 1e8 / 510e6:.2e}\n'
        lines += f'rayon de schwarschild (m),{sch_rad:.2e}\n'
        lines += f'rayon de schwarschild molaire (micro m/mol),{molar_sch_rad * 1e6:.2f}\n'
        f.write(lines)

def generate_report(cookies: list) -> None:
    global OUT_DIR, CURR_DIR
    """génère un rapport PDF à partir d'un template typst"""
    from json import dumps
    infos = {
        "date": options.date,
        "author": options.author,
        "dest": options.dest,
        "nb_cookies": len(cookies),
    }
    sys_inputs = {
        "infos": dumps(infos)
    }
    import typst
    typst.compile(input=f"{CURR_DIR}/../templates/main.typ", output=f'{OUT_DIR}/report.pdf', root=f"{CURR_DIR}/..", sys_inputs=sys_inputs)


def main(img_to_process: str) -> None:
    global MIN_D, MAX_D, CAL_SIZE, CURR_DIR, OUT_DIR
    img = cv2.imread(f'{img_to_process}')
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
    cv2.imwrite(f'{OUT_DIR}/resdst.png', dst)
    cv2.imwrite(f'{OUT_DIR}/resmask.png', mask)
    cv2.imwrite(f'{OUT_DIR}/res.png', img)

    generate_diameters(diams, roundnesses, cookies, total_area)

    plt.hist(diams, bins=15)
    plt.xlabel('Diamètre (cm)')
    plt.ylabel('Fréquence')
    plt.title('Distribution des diamètres')
    plt.savefig(f'{OUT_DIR}/diam_histogram.png')
    plt.close()

    plt.hist(roundnesses, bins=15)
    plt.xlabel('Rotondité')
    plt.ylabel('Fréquence')
    plt.title('Distribution des rotondités')
    plt.savefig(f'{OUT_DIR}/roundness_histogram.png')
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
    plt.savefig(f'{OUT_DIR}/roundness_diam_scatter.png')

    generate_report(cookies=cookies)

    print('done (hopefully)')


if __name__ == "__main__":
    from datetime import datetime
    parser = OptionParser(usage="Usage: %prog [options] FILE", description="Automates the detection and analysis of cookies in an image.")
    parser.add_option("--date", dest="date", help="Date of the analysis, use dd/mm/yyyy format. Leave empty for today", metavar="DATE", default=datetime.now().strftime("%d/%m/%Y"))
    parser.add_option("--author", dest="author", help="Name of the author of the cookies", metavar="AUTHOR", default="Anonymous")
    parser.add_option("--dest", dest="dest", help="Name of the recipient of the cookies", metavar="DEST", default="Anonymous")
    parser.add_option("--reference", dest="reference", help="Reference object length in cm for calibration (default: 90 cm)", metavar="REFERENCE", type="float", default=CAL_SIZE)
    parser.add_option("--conf", dest="confidence", type="float", help="Confidence threshold for cookie detection (between 0 and 1)", metavar="CONFIDENCE", default=0.8)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Incorrect number of arguments. Please provide the path to the image file.")
    print("Options:", options)
    print("Arguments:", args)

    main(args[0])