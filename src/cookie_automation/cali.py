import cv2
import numpy as np

class Calibrator:
    def __init__(self) -> None:
        self.screen_pos = []

    def callback(self, event, x: float, y: float, flags, param) -> None:
        if event == cv2.EVENT_FLAG_LBUTTON:
            if len(self.screen_pos) >= 2:
                self.screen_pos = []
            self.screen_pos.append([x, y])

    def get_calib(self, img, length_cm: float) -> float:
        print('Cliquez sur 2 points espacés de', length_cm, 'cm (vous pouvez recliquer si vous vous êtes trompé, cela réinitialisera les points)')
        print("Ensuite appuyer sur n'importe quelle touche")
        cv2.imshow('pspsps', img)
        cv2.setMouseCallback('pspsps', self.callback)
        cv2.waitKey(0)
        p1, p2 = self.screen_pos[:2]
        (x1,y1), (x2, y2) = p1, p2
        length_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return length_cm / length_px