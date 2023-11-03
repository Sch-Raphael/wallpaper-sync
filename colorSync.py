from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
from colorthief import ColorThief
from PIL import Image
import colorsys
import time
import os

# get the wallpaper path
wallpaper_path = (os.getenv('APPDATA') + "\\Microsoft\\Windows\\Themes\\WallpaperEngineOverride.jpg")
wallpaper_dir  = (os.getenv('APPDATA') + "\\Microsoft\\Windows\\Themes")

last_image_hash = None

# change the color of every device
def colorChange(client, colorR, colorG, colorB):
    # get all devices
    devices = client.devices
    
    # init color object
    color = RGBColor(colorR, colorG, colorB)
    
    for device in devices:
        device.set_color(color)
        print(device)
        
        
# get the dominant color from the background image
def get_color():
    # Get the top 20 palette colors from wallpaper
    color_thief = ColorThief(wallpaper_path)
    palette = color_thief.get_palette(color_count=20, quality=8)
    
    max_difference = 70

    # White color on failure
    final = (228, 226, 226)

    # Find the color with the biggest difference between its RGB values
    for color in palette:
        dif1 = abs(color[0] - color[1])
        dif2 = abs(color[1] - color[2])
        dif3 = abs(color[0] - color[2])
        if dif1 > max_difference or dif2 > max_difference or dif3 > max_difference:
            final = color
            break

    # Converting to the HSV color space and setting to 100% Saturation and 75% Value for the best colors for RGB
    hsv_col = colorsys.rgb_to_hsv(final[0] / 255, final[1] / 255, final[2] / 255)
    hsv_col = (hsv_col[0], 1, 0.75)

    # Convert back to RGB for LEDs
    final = colorsys.hsv_to_rgb(hsv_col[0], hsv_col[1], hsv_col[2])
    final = (int(final[0] * 255), int(final[1] * 255), int(final[2] * 255))

    return (final)


def change(client):    
    # get wallpaper color
    colorRGB = get_color()
    print(colorRGB)
    
    # set lighting
    colorChange(client, colorRGB[0], colorRGB[1], colorRGB[2])
    
    
    
# image change event handler
class ImageChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("WallpaperEngineOverride.jpg"):
            global last_image_hash
            # Compute the hash of the new image
            new_image = Image.open(wallpaper_path)
            new_image_hash = hash(new_image.tobytes())
            if new_image_hash != last_image_hash:
                last_image_hash = new_image_hash
                change()
    
    
def start():
    # connect to openRGB SDK
    client = OpenRGBClient("127.0.0.1", 8000, 'Wallpaper Sync')    
    
    # run on start
    change(client)
    
    # observer on image change
    event_handler = ImageChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=wallpaper_dir)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


start_fails = 0
if __name__ == "__main__":
    try:
        start()
    except:
        if start_fails < 20:
            start_fails = +1
            start()
            time.sleep(2)
        else:
            exit()