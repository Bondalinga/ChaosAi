import os
import sys
import time
import numpy as np
import torch
import mss
import cv2
import controller
from pynput import mouse, keyboard

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Global settings
aiming_enabled = False
auto_shoot_enabled = False
debug_mode = False
FOV = 300
sensitivity_scale = 0.2 
assistance = 0.05  

# ASCII Art for Banner
ascii_art = r"""
 ______  ______                     
/\  _  \/\__  _\ [From Bondalinga]  
\ \ \L\ \/_/\ \/     ___ ___ /\_\   
 \ \  __ \ \ \ \   /' __` __`\/\ \  
  \ \ \/\ \ \_\ \__/\ \/\ \/\ \ \ \ 
   \ \_\ \_\/\_____\ \_\ \_\ \_\ \_\
    \/_/\/_/\/_____/\/_/\/_/\/_/\/_/
"""

def print_status():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{ascii_art}")
    print(f'F1 Aim Assistance: {"Enabled" if aiming_enabled else "Disabled"}')
    print(f'F2 Auto-shoot: {"Enabled" if auto_shoot_enabled else "Disabled"}')
    print(f'Sensitivity: {sensitivity_scale:.2f}')
    print(f'Assistance: {assistance:.2f}')

def on_activate_aiming():
    global aiming_enabled
    aiming_enabled = not aiming_enabled
    print_status()

def on_activate_auto_shoot():
    global auto_shoot_enabled
    auto_shoot_enabled = not auto_shoot_enabled
    print_status()

def on_increase_sensitivity():
    global sensitivity_scale
    sensitivity_scale += 0.01
    print_status()

def on_decrease_sensitivity():
    global sensitivity_scale
    sensitivity_scale = max(0.01, sensitivity_scale - 0.01)
    print_status()

def on_increase_assistance():
    global assistance
    assistance += 0.005
    print_status()

def on_decrease_assistance():
    global assistance
    assistance = max(0.005, assistance - 0.005)
    print_status()

def setup_key_listeners():
    from pynput.keyboard import GlobalHotKeys

    hotkeys = GlobalHotKeys({
        '<f1>': on_activate_aiming,
        '<f2>': on_activate_auto_shoot,
        '<up>': on_increase_sensitivity,
        '<down>': on_decrease_sensitivity,
        '<left>': on_decrease_assistance,
        '<right>': on_increase_assistance,
    })
    hotkeys.start()
    return hotkeys

def is_point_in_bbox(point_x, point_y, bbox):
    return bbox['left'] <= point_x <= bbox['left'] + bbox['width'] and bbox['top'] <= point_y <= bbox['top'] + bbox['height']

def mouse_click_handler(x, y, button, pressed):
    global right_mouse_pressed
    if button == mouse.Button.right:
        right_mouse_pressed = pressed

def keyboard_press_handler(key):
    global alt_pressed
    try:
        if key == keyboard.Key.alt:
            alt_pressed = True
    except AttributeError:
        pass

def keyboard_release_handler(key):
    global alt_pressed
    try:
        if key == keyboard.Key.alt:
            alt_pressed = False
    except AttributeError:
        pass

def main():
    global screen_center_x, screen_center_y, aiming_enabled, auto_shoot_enabled, FOV, bbox
    conf_threshold = 0.35
    offset_ratio = 0.10

    print_status()

    sct = mss.mss()
    monitor = sct.monitors[0] 

    screen_width = int(monitor['width'])
    screen_height = int(monitor['height'])
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2

    bbox = {'top': (screen_center_y - (FOV // 2)),
            'left': (screen_center_x - (FOV // 2)),
            'width': FOV,
            'height': FOV}

    cv2.namedWindow("Object Detection", cv2.WINDOW_NORMAL)

    while True:
        try:
            start_time = time.time()

            screenshot = sct.grab(bbox)
            img = np.array(screenshot)

            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            results = model(img_bgr)
            detections = results.pred[0][results.pred[0][:, 4] > conf_threshold]
            detections = sorted(detections, key=lambda x: x[4], reverse=True)

            detected = False
            closest_bbox = None
            top_middle_x_closest = screen_center_x
            top_middle_y_closest = screen_center_y

            if detections is not None and len(detections):
                for detection in detections:
                    *xyxy, conf, cls = detection.cpu().numpy()

                    box_width = xyxy[2] - xyxy[0]
                    box_height = xyxy[3] - xyxy[1]

                    offset = int(box_height * offset_ratio)

                    top_x_relative = int((xyxy[0] + xyxy[2]) / 2)
                    top_y_relative = int(xyxy[1] + offset)

                    top_middle_x = bbox['left'] + top_x_relative
                    top_middle_y = bbox['top'] + top_y_relative

                    bbox_coords = {
                        'left': int(xyxy[0]) + bbox['left'],
                        'top': int(xyxy[1]) + bbox['top'],
                        'width': int(box_width),
                        'height': int(box_height)
                    }

                    cv2.rectangle(img_bgr, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
                    cv2.putText(img_bgr, f'{int(cls)}: {conf:.2f}', (int(xyxy[0]), int(xyxy[1]) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                    deadzone_width = 0.05 * bbox_coords['width']
                    deadzone_height = 0.05 * bbox_coords['height']

                    delta_x = abs(top_middle_x - screen_center_x)
                    delta_y = abs(top_middle_y - screen_center_y)
                    distance = np.sqrt(delta_x ** 2 + delta_y ** 2)

                    if closest_bbox is None or distance < np.sqrt((top_middle_x_closest - screen_center_x) ** 2 + (top_middle_y_closest - screen_center_y) ** 2):
                        closest_bbox = bbox_coords
                        top_middle_x_closest = top_middle_x
                        top_middle_y_closest = top_middle_y
                        detected = True

            if detected:
                if aiming_enabled and right_mouse_pressed:
                    if (abs(top_middle_x_closest - screen_center_x) > deadzone_width or
                        abs(top_middle_y_closest - screen_center_y) > deadzone_height):

                        delta_x = top_middle_x_closest - screen_center_x
                        delta_y = top_middle_y_closest - screen_center_y

                        delta_x *= sensitivity_scale
                        delta_y *= sensitivity_scale

                        mouse_controller.mouse_move(delta_x, delta_y, assistance)

                if auto_shoot_enabled and alt_pressed:
                    if is_point_in_bbox(screen_center_x, screen_center_y, closest_bbox):
                        mouse_controller.click()

            end_time = time.time()
            fps = 1 / (end_time - start_time)

            cv2.putText(img_bgr, f'FPS: {fps:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            cv2.imshow("Object Detection", img_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if debug_mode:
                print(f"FPS: {fps:.2f}")

        except Exception as e:
            print(f"Error: {e}")

    cv2.destroyAllWindows()


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    try:
        model = torch.hub.load('ultralytics/yolov5', 'custom', path='model.pt', source='local').to(device).eval()
    except Exception as e:
        print(f"Failed to load model: {e}")
        sys.exit()

    mouse_controller = controller.CrosshairMover()
    right_mouse_pressed = False
    alt_pressed = False

    # Setup listeners
    mouse_listener = mouse.Listener(on_click=mouse_click_handler)
    mouse_listener.start()
    keyboard_listener = keyboard.Listener(on_press=keyboard_press_handler, on_release=keyboard_release_handler)
    keyboard_listener.start()
    hotkeys = setup_key_listeners()

    main()

    # Stop listeners
    mouse_listener.stop()
    keyboard_listener.stop()
    hotkeys.stop()
