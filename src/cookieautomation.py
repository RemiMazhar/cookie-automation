from functools import cmp_to_key
import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.stats import linregress
from cali import Calibrator
from os import path
from pathlib import Path
from optparse import OptionParser
from ultralytics import YOLO

# Path setup
CURR_DIR = path.dirname(path.abspath(__file__)).replace('\\', '/')
OUT_DIR = f"{CURR_DIR}/out"
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

CAL_SIZE: float = 90 # longueur du trait de calibration (pour moi le bord de la table) en cm
BIBLICALLY_ACCURATE_COOKIE_SPACING: float = 30 # espacement minimum entre cookies en cm pour qu'ils soient considérés comme sur des "lignes" différentes


# algo pour numéroter les cookies en sens de lecture
# enfin à peu près, pcq on en trouve jamais 2 exactement à la même ordonnée
# donc ya des histoires d'approximations
# bref c'est une relation d'ordre bricolée pour rendre la numérotation à peu près lisible
def cmpZ2(coords1: tuple[float, float], coords2: tuple[float, float], spacing_px: float) -> int:
    x1, y1 = coords1
    x2, y2 = coords2
    #print(f'Comparing cookies at ({x1:.2f}, {y1:.2f}) and ({x2:.2f}, {y2:.2f}) with spacing {spacing_px:.2f}')
    if abs(y1 - y2) <= spacing_px:
        return -1 if x1 < x2 else (1 if x1 > x2 else 0)
    else:
        return -1 if y1 < y2 else 1
    
def cmpCookies(spacing_px: float):
    """Clairement, encore une raison de pas utiliser python..."""
    def compare(cookie1: tuple, cookie2: tuple) -> int:
        coords1, d1, _ = cookie1
        coords2, d2, _ = cookie2
        return cmpZ2(coords1, coords2, spacing_px)
    return compare


def generate_diameters(diams: list, roundnesses: list, cookies: list, total_area: float) -> None:
    """génère un fichier diameters.csv avec les diamètres et rotondités des cookies détectés, ainsi que des statistiques diverses"""
    global OUT_DIR
    avg_diam = np.average(diams)
    std_diams = np.std(diams)
    total_mass = int(input("Total mass:"))  
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
    from json import dumps # AT: Je pourrais use orjson pour avoir des vraies perf mais ça sert à rien ici pour dump 4 petits champs
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
    global CURR_DIR, OUT_DIR, BIBLICALLY_ACCURATE_COOKIE_SPACING, options
    img = cv2.imread(f'{img_to_process}')
    if img.shape[1] < img.shape[0] : img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) # format paysage pcq j'ai décidé # AT: Bon ok
    img = cv2.resize(img, (800, 600), interpolation=cv2.INTER_NEAREST)

    c = Calibrator()
    scale = c.get_calib(img, options.reference)
    print(f'échelle: {1/scale:.2f} px/cm')

    model = YOLO("runs/segment/train3/weights/best.onnx")  # load a pretrained YOLO model
    results = model.predict(source=img, conf=options.confidence, save=False, device="cpu", show=False, imgsz=1920)  # predict on an image

    total_mask = np.zeros(img.shape[:2], dtype=np.uint8)

    diams = []
    ctrs = []
    roundnesses = []
    total_area = 0
    for r in results:
        if r.masks is None:
            print("No masks found in the image.")
            continue

        masks = r.masks
        for mask in masks.data:
            # Convert mask to uint8 (0/255) and resize to match original image size
            mask_np = mask.cpu().numpy().astype(np.uint8) * 255
            mask_resized = cv2.resize(mask_np, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

            # Add overlay color to the original image with transparency
            overlay = img.copy()
            overlay[mask_resized == 255] = (0, 255, 0)  # Green color for mask
            alpha = 0.2  # Transparency factor
            img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
            
            # Combine masks
            total_mask = cv2.bitwise_or(total_mask, mask_resized)

            # Calculate properties directly from mask
            binary_mask = (mask_resized == 255).astype(np.uint8)
            
            # Calculate area (count non-zero pixels)
            contour_area = np.sum(binary_mask)
            
            # Calculate moments from mask
            M = cv2.moments(binary_mask)
            
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # Calculate diameter
                d = 2 * np.sqrt(contour_area / np.pi) * scale
                total_area += contour_area * scale**2
                
                # Calculate roundness using minimum enclosing circle
                y_coords, x_coords = np.where(binary_mask > 0)
                if len(x_coords) > 0:
                    points = np.column_stack((x_coords, y_coords))
                    (_, _), radius = cv2.minEnclosingCircle(points.astype(np.float32))
                    roundness = contour_area / (np.pi * radius**2)
                    
                    diams.append(d)
                    ctrs.append((cX, cY))
                    roundnesses.append(roundness)
    if not results or all(r.masks is None for r in results):
        print("No cookies detected in the image.")
        return


    # Calculate minimum distance between all cookies
    min_distance = float('inf')
    if len(ctrs) > 1:
        for i in range(len(ctrs)):
            for j in range(i + 1, len(ctrs)):
                dist = np.sqrt((ctrs[i][0] - ctrs[j][0])**2 + (ctrs[i][1] - ctrs[j][1])**2) * scale
                min_distance = min(min_distance, dist)
        #print(f'Minimum distance between cookies: {min_distance:.2f} cm')
        if min_distance < BIBLICALLY_ACCURATE_COOKIE_SPACING:
            BIBLICALLY_ACCURATE_COOKIE_SPACING = min_distance
            print(f'Adjusted BIBLICALLY_ACCURATE_COOKIE_SPACING to {BIBLICALLY_ACCURATE_COOKIE_SPACING:.2f} cm')
    else:
        pass

    cookies = list(zip(ctrs, diams, roundnesses))
    spacing_in_pixels = BIBLICALLY_ACCURATE_COOKIE_SPACING / scale if min_distance != float('inf') else BIBLICALLY_ACCURATE_COOKIE_SPACING
    cookies.sort(key=cmp_to_key(cmpCookies(spacing_in_pixels)))
    


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
    cv2.imwrite(f'{OUT_DIR}/resmask.png', total_mask)
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
    x_range = np.linspace(min(diams), max(diams), 100)
    ys = np.exp(regress.intercept + regress.slope * x_range)
    print(f'{100 * regress.slope:.1f}% par cm')
    lbl = f"{'+' if regress.slope >= 0 else ''}{100 * regress.slope:.1f} % de rotondité par cm"
    plt.plot(x_range, ys, color='orange', label=lbl)
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
    if len(args) < 1:
        parser.error("Incorrect number of arguments. Please provide the path to the image file.")
    print("Options:", options)
    print("Arguments:", args)

    for arg in args:
        main(arg)