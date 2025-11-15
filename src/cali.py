import cv2
import numpy as np

class Calibrator:
    def __init__(self):
        self.screen_pos = []

    def callback(self, event, x: float, y: float, flags, param):
        if event == cv2.EVENT_FLAG_LBUTTON:
            self.screen_pos.append([x, y])

    def get_zone(self, img, length_cm: float):
        print('cliquez sur 2 points espacés de', length_cm, 'cm puis sur N points qui définissent un polygone qui contient tous les cookies')
        print("ensuite appuyer sur n'importe quelle touche")
        cv2.imshow('pspsps', img)
        cv2.setMouseCallback('pspsps', self.callback)
        cv2.waitKey(0)
        p1, p2 = self.screen_pos[:2]
        (x1,y1), (x2, y2) = p1, p2
        length_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return self.screen_pos[2:], length_cm / length_px