import asyncio
from enum import IntEnum
import json
import os
import random
import threading
from PIL import Image, ImageDraw, ImageFont

from cgcpluginlib import cpl, pluginrequest
from cgcpluginlib.ostreamvisual import OStreamVisual
from cgcpluginlib.general import ColourIndexType, LabelType
from cgcpluginlib.ostreamheatmap import OStreamHeatmap, HeatmapInfo
from cgcpluginlib.ostreamalphabitmap import OStreamAlphaBitMap
from cgcpluginlib.istreamgeolocation import parse_IStreamGeoLocation
from cgcpluginlib.visualobject import VoBox, VoClickMap, ClickBox

TIMEOUT = 120000
IMAGE_BUFFER = 10

DEFAULT_UP_BUTTON = ClickBox(
    xmin=1800,
    ymin=370,
    xmax=1900,
    ymax=470,
    clickable=json.dumps({
        "action": "increment",
        "state": 5,
    })
)

DEFAULT_DOWN_BUTTON = ClickBox(
    xmin=1800,
    ymin=610,
    xmax=1900,
    ymax=710,
    clickable=json.dumps({
        "action": "decrement",
        "state": 5,
    })
)


class IoChannelId(IntEnum):
    OBJECT_DETECTION_CHANNEL_ID = 0
    HEATMAP_CHANNEL_ID = 1
    GEO_OVERLAY_CHANNEL_ID = 2
    UI_CHANNEL_ID = 3
    USER_FORM_CHANNEL_ID = 4


class ImageProcessor:
    """
    In this example, object detection and heatmap are processed in process_jpeg, which runs in a single thread. 
    Consider using multiple threads for improved performance if synchronisation is not required.
    """

    def __init__(self, object_detection_folder, heatmap_folder, heatmap_image_folder):
        self.object_detection_folder = object_detection_folder
        self.heatmap_folder = heatmap_folder
        self.heatmap_image_folder = heatmap_image_folder
        self.count = 0

    def process_jpeg(self, jpeg_path):
        try:
            heatmap_string = self._generate_heatmap(jpeg_path)
        except Exception as e:
            print("ImageProcessor generate heatmap: Exception: ", e)
            return

        try:
            object_detection_string = self._detect_objects(jpeg_path)
        except Exception as e:
            print("ImageProcessor detect objects: Exception: ", e)
            return

        if heatmap_string is not None:
            cpl.write_string_to_file(
                heatmap_string, self.heatmap_folder + "/" + str(self.count) + ".json")
        else:
            print("heatmap_string is None")

        if object_detection_string is not None:
            cpl.write_string_to_file(
                object_detection_string, self.object_detection_folder + "/" + str(self.count) + ".json")
            self.count += 1
        else:
            print("object_detection_string is None")

    def _generate_heatmap(self, image_file):
        """
        Generate heatmap image from image and return OStreamHeatmap json string with image url pointing to saved image file
        """
        img = Image.open(image_file).convert('L')
        output_file_path = self.heatmap_image_folder + \
            "/heatmap" + str(self.count) + ".jpg"
        img.save(output_file_path)

        heatmap_info = HeatmapInfo(
            scalingFactor=100.0,
            scalingUnit="%"
        )

        heatmap: OStreamHeatmap = OStreamHeatmap(
            desc="greyscale heatmap",
            heatmapInfo=heatmap_info,
            imageUrl=output_file_path
        )

        return heatmap.json()

    def _detect_objects(self, image_file):
        """
        Detect objects from image and return OStreamVisual json string
        """
        # Insert object detection code here...

        # Detect objects from image and then populate OStreamVisual with VoBox objects
        xmin = 300 + random.randrange(-50, 50)
        ymin = 300 + random.randrange(-50, 50)
        xmax = 600 + random.randrange(-50, 50)
        ymax = 600 + random.randrange(-50, 50)
        """
        TUTORIAL 01
        Try changing the label, label type and clickable below:

        label:          "person 1"          -> "boat 1"
        label type:     LabelType.H1.value  -> LabelType.H3.value
        clickable:      "clicked person 1"  -> "clicked boat 1"

        You can also try changing other fields such as xmin, ymin, xmax, ymax, outlineColourIndex, fill, etc.
        """
        box1: VoBox = VoBox(
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
            filterValue=0.8,
            name="person 1",
            labelType=LabelType.H1,
            outlineColourIndex=ColourIndexType.C15,
            clickable="clicked person 1"
        )

        xmin = 900 + random.randrange(-50, 50)
        ymin = 400 + random.randrange(-50, 50)
        xmax = 1200 + random.randrange(-50, 50)
        ymax = 700 + random.randrange(-50, 50)

        box2: VoBox = VoBox(
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
            filterValue=0.8,
            name="person 2",
            labelType=LabelType.H1,
            outlineColourIndex=ColourIndexType.C15,
            clickable="clicked person 2"
        )

        output: OStreamVisual = OStreamVisual(
            desc="optical detection",
            refWidth=1920,
            refHeight=1080,
            boxes=[box1, box2]
        )

        return output.json()


class GeolocationProcessor():
    def __init__(self, geo_overlay_folder, geo_overlay_image_folder):
        self.geo_overlay_folder = geo_overlay_folder
        self.geo_overlay_image_folder = geo_overlay_image_folder
        self.count = 0

    def process_file(self, file_path):
        try:
            geo_overlay_string = self._convert_geo_to_overlay(file_path)
        except Exception as e:
            print("GeolocationProcessor convert geo to overlay: Exception: ", e)
            return

        if geo_overlay_string is not None:
            cpl.write_string_to_file(
                geo_overlay_string, self.geo_overlay_folder + "/" + str(self.count) + ".json")
            self.count += 1
        else:
            print("geo_overlay_string is None")

    def _convert_geo_to_overlay(self, file_path):
        """
        Display geolocation as an overlay
        """
        iStreamGeolocation = parse_IStreamGeoLocation(file_path)

        if iStreamGeolocation.position is None:
            print("iStreamGeolocation.position is None")
            return None

        if iStreamGeolocation.position.geolocation is None or iStreamGeolocation.position.angular is None:
            print(
                "iStreamGeolocation.position.geolocation or iStreamGeolocation.position.angular is None")
            return None

        """
        TUTORIAL 02
        Try changing the strings below to reference different fields in the iStreamGeolocation object:

        string1:    "Lat: {iStreamGeolocation.position.geolocation.latitude}°"          -> "Time: {iStreamGeolocation.time}"
        string2:    "Lon: {iStreamGeolocation.position.geolocation.longitude}°"         -> "Roll: {iStreamGeolocation.position.angular.roll}°"
        string3:    "Altitude: {iStreamGeolocation.position.geolocation.altitude} m"    -> "Pitch: {iStreamGeolocation.position.angular.pitch}°"
        string4:    "Heading: {iStreamGeolocation.position.angular.yaw}°"               -> "Yaw: {iStreamGeolocation.position.angular.yaw}°"

        You can also change the overlay design by changing the font and the coordinates of the drawn objects.
        Font must be provided as a .ttf file in the same directory as main.py in the plugin Dockerfile when using the PIL library.
        """
        string1 = f"Lat: {iStreamGeolocation.position.geolocation.latitude}°"
        string2 = f"Lon: {iStreamGeolocation.position.geolocation.longitude}°"
        string3 = f"Altitude: {iStreamGeolocation.position.geolocation.altitude} m"
        string4 = f"Heading: {iStreamGeolocation.position.angular.yaw}°"

        """
        Plug-in framework treats values <16 as transparent.
        Grayscale images are recommended for overlays.
        """
        img = Image.new('L', (1920, 1080), (0))
        font = ImageFont.truetype("arial.ttf", 40)
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle((1300, 810, 1900, 1060), fill=(
            50), outline=(200), width=8, radius=20)
        draw.text((1320, 830), string1, fill=(200),
                  font=font, anchor=None, spacing=0, align="left")
        draw.text((1320, 880), string2, fill=(200),
                  font=font, anchor=None, spacing=0, align="left")
        draw.text((1320, 930), string3, fill=(200),
                  font=font, anchor=None, spacing=0, align="left")
        draw.text((1320, 980), string4, fill=(200),
                  font=font, anchor=None, spacing=0, align="left")

        output_file_path = self.geo_overlay_image_folder + \
            "/alphabitmap" + str(self.count) + ".jpg"
        img.save(output_file_path)

        output: OStreamAlphaBitMap = OStreamAlphaBitMap(
            desc=f"geolocation overlay #{str(self.count)}",
            imageUrl=output_file_path
        )

        return output.json()


class UiProcessor():
    def __init__(self, ui_folder, ui_image_folder):
        self.ui_folder = ui_folder
        self.ui_image_folder = ui_image_folder
        self.count = 0

    def process_file(self, file_path):
        try:
            ui_string = self._update_ui(file_path)
        except Exception as e:
            print("UiProcessor update ui: Exception: ", e)
            return

        if ui_string is not None:
            cpl.write_string_to_file(
                ui_string, self.ui_folder + "/" + str(self.count) + ".json")
            self.count += 1
        else:
            print("geo_overlay_string is None")

    def _update_ui(self, file_path):
        """
        Update the ui in response to user input
        """
        action = None
        state = None

        """
        TUTORIAL 03
        Try adding another button that resets the state to 5:

        Insert the following code in the appropriate places below marked with "# TUTORIAL 03 - perform step X here"

        1. Define a new click box
        ```
        reset_button: ClickBox = ClickBox(
            xmin=1800,
            ymin=850,
            xmax=1900,
            ymax=950,
            clickable=json.dumps({
                "action": "reset",
                "state": 5,
                })
            )
        ```

        2. Add an if statement to handle the "reset" action
        ```
        if action == "reset":
            print(
                f"resetting state to 5")

            state = 5
        ```

        3. Add an if statement to draw the reset button and add it to the clickBoxes list
        ```
        if state != 5:
            draw.rounded_rectangle((reset_button.xmin, reset_button.ymin, reset_button.xmax, reset_button.ymax), fill=(
                50), outline=(200), width=8, radius=20)
            draw.text((1830, 880), "R", fill=(200), font=font)

            clickBoxes.append(reset_button)

        """

        # TUTORIAL 03 - perform step 1 here

        with open(file_path) as f:
            data = json.load(f)
            action = data['action']
            state = data['state']

        if action == "increment":
            print(
                f"incrementing {state} by 1")

            state += 1

        if action == "decrement":
            print(
                f"decrementing {state} by 1")

            state -= 1

        # TUTORIAL 03 - perform step 2 here

        # Update button clickable state
        up_button: ClickBox = DEFAULT_UP_BUTTON
        down_button: ClickBox = DEFAULT_DOWN_BUTTON
        up_button.clickable = json.dumps({
            "action": "increment",
            "state": state
        })
        down_button.clickable = json.dumps({
            "action": "decrement",
            "state": state
        })

        # Draw UI
        img = Image.new('L', (1920, 1080), (0))
        font = ImageFont.truetype("arial.ttf", 40)
        draw = ImageDraw.Draw(img)

        # Draw box with current state
        draw.rounded_rectangle((1800, 490, 1900, 590), fill=(
            50), width=8, radius=20)
        draw.text((1830, 520), f" {str(state)}",
                  fill=(200), font=font)

        clickBoxes = []

        # If state <9 then draw up button
        if state < 9:
            draw.rounded_rectangle((DEFAULT_UP_BUTTON.xmin, DEFAULT_UP_BUTTON.ymin, DEFAULT_UP_BUTTON.xmax, DEFAULT_UP_BUTTON.ymax), fill=(
                50), outline=(200), width=8, radius=20)
            draw.text((1830, 400), "▲", fill=(200), font=font)

            clickBoxes.append(up_button)

        # If state > 1 then draw down button
        if state > 1:
            draw.rounded_rectangle((DEFAULT_DOWN_BUTTON.xmin, DEFAULT_DOWN_BUTTON.ymin, DEFAULT_DOWN_BUTTON.xmax, DEFAULT_DOWN_BUTTON.ymax), fill=(
                50), outline=(200), width=8, radius=20)
            draw.text((1830, 640), "▼", fill=(200), font=font)

            clickBoxes.append(down_button)

        # TUTORIAL 03 - perform step 3 here

        output_file_path = self.ui_image_folder + \
            "/ui" + str(self.count) + ".jpg"
        img.save(output_file_path)

        voClickMap: VoClickMap = VoClickMap(
            clickBoxes=clickBoxes,
            clickPolygons=[]
        )

        output: OStreamAlphaBitMap = OStreamAlphaBitMap(
            desc=f"ui #{str(self.count)}",
            imageUrl=output_file_path,
            clickMap=voClickMap
        )

        return output.json()


def initialise_static_ui(ui_output_folder: str, ui_image_folder: str):
    """
    Generate the first UI image and save it to the UI folder for display. Subsequent UI images will be generated by listening to the UI input channel.
    """
    img = Image.new('L', (1920, 1080), (0))
    font = ImageFont.truetype("arial.ttf", 40)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((DEFAULT_UP_BUTTON.xmin, DEFAULT_UP_BUTTON.ymin, DEFAULT_UP_BUTTON.xmax, DEFAULT_UP_BUTTON.ymax), fill=(
        50), outline=(200), width=8, radius=20)
    draw.text((1830, 400), "▲", fill=(200), font=font)

    draw.rounded_rectangle((1800, 490, 1900, 590), fill=(
        50), width=8, radius=20)
    draw.text((1830, 520), " 5", fill=(200), font=font)

    draw.rounded_rectangle((DEFAULT_DOWN_BUTTON.xmin, DEFAULT_DOWN_BUTTON.ymin, DEFAULT_DOWN_BUTTON.xmax, DEFAULT_DOWN_BUTTON.ymax), fill=(
        50), outline=(200), width=8, radius=20)
    draw.text((1830, 640), "▼", fill=(200), font=font)

    output_file_path = ui_image_folder + "/initial_ui.jpg"
    img.save(output_file_path)

    voClickMap: VoClickMap = VoClickMap(
        clickBoxes=[
            DEFAULT_UP_BUTTON,
            DEFAULT_DOWN_BUTTON
        ],
        clickPolygons=[]
    )

    output: OStreamAlphaBitMap = OStreamAlphaBitMap(
        desc="initial_ui",
        imageUrl=output_file_path,
        clickMap=voClickMap
    )

    cpl.write_string_to_file(
        output.json(), ui_output_folder + "/initial_ui.json")


def cleanup_image_folders(image_folders, buffer):
    while True:
        for image_folder in image_folders:
            files = os.scandir(image_folder)
            # Sort files by modification time, oldest first
            files = sorted(files, key=lambda f: f.stat().st_mtime)

            if len(files) > buffer:
                # Delete oldest files
                for file in files[:-buffer]:
                    os.remove(file.path)


def main():
    ##########################
    #   *** SETUP ***
    ##########################
    args = cpl.parse_args()

    request_file = args.request_file
    # result_folder = args.result_folder
    # result_file = args.result_file
    stop_file = args.stop_file
    input_channel_folder = args.input_channel_folder
    output_channel_folder = args.output_channel_folder
    telemetry_stream_folder = args.telemetry_stream_folder

    request = pluginrequest.parse_plugin_request(request_file)

    # TELEMETRY CHANNELS - telemetry will be written to these folders as either json or jpeg files
    # telemetryFeeds[idx]: currently only one telemetry feed per vehicle is supported. Use idx=0
    # cameraFeedsImageFolders[idx]: camera feed image folders are ordered by camera index starting from idx=0
    camera_feeds_image_folder_0 = f"{telemetry_stream_folder}/{request.telemetryFeeds[0].cameraFeedsImageFolders[0]}"
    geolocation_folder = f"{telemetry_stream_folder}/{request.telemetryFeeds[0].geolocationFolder}"

    # INPUT CHANNELS - input from cgc webconsole will be written to these folders as json files matching the channel's userInputSchema
    user_form_folder = f"{input_channel_folder}/{request.inputChannelFolder(IoChannelId.USER_FORM_CHANNEL_ID.value)}"
    ui_input_folder = f"{input_channel_folder}/{request.inputChannelFolder(IoChannelId.UI_CHANNEL_ID.value)}"

    # OUTPUT CHANNELS - output from this plugin will be written to these folders as json files, they must match the cgc ostream types
    geo_overlay_folder = f"{output_channel_folder}/{request.outputChannelFolder(IoChannelId.GEO_OVERLAY_CHANNEL_ID.value)}"
    ui_output_folder = f"{output_channel_folder}/{request.outputChannelFolder(IoChannelId.UI_CHANNEL_ID.value)}"

    object_detection_folder = f"{output_channel_folder}/{request.outputChannelFolder(IoChannelId.OBJECT_DETECTION_CHANNEL_ID.value)}"
    heatmap_folder = f"{output_channel_folder}/{request.outputChannelFolder(IoChannelId.HEATMAP_CHANNEL_ID.value)}"

    # OUTPUT IMAGE FOLDERS - absolute path to store images that are referenced by output channel outputs
    heatmap_image_folder = f"{output_channel_folder}/images/heatmap"
    geo_overlay_image_folder = f"{output_channel_folder}/images/geo_overlay"
    ui_image_folder = f"{output_channel_folder}/images/ui"

    pluginrequest.initialise_folders([camera_feeds_image_folder_0, geolocation_folder, user_form_folder, ui_input_folder, ui_output_folder,
                                     geo_overlay_folder, object_detection_folder, heatmap_folder, heatmap_image_folder, geo_overlay_image_folder, ui_image_folder])

    ##########################
    #   *** RUN ***
    ##########################
    image_processor = ImageProcessor(
        object_detection_folder, heatmap_folder, heatmap_image_folder)
    geolocation_processor = GeolocationProcessor(
        geo_overlay_folder, geo_overlay_image_folder)
    ui_processor = UiProcessor(ui_output_folder, ui_image_folder)

    stop_observer = cpl.start_stop_file_watcher(stop_file)
    cpl.start_image_watcher(
        camera_feeds_image_folder_0, stop_file, callback=image_processor.process_jpeg)
    cpl.start_json_watcher(
        geolocation_folder, stop_file, callback=geolocation_processor.process_file)
    cpl.start_json_watcher(
        ui_input_folder, stop_file, callback=ui_processor.process_file)

    cleanup_thread = threading.Thread(target=cleanup_image_folders, args=(
        [heatmap_image_folder, geo_overlay_image_folder, ui_image_folder], IMAGE_BUFFER))
    cleanup_thread.daemon = True
    cleanup_thread.start()
    print("Clean up thread started")

    initialise_static_ui(ui_output_folder, ui_image_folder)

    cpl.join_stop_file_watcher(stop_observer)
    cleanup_thread.join()
    os._exit(0)


if __name__ == "__main__":
    asyncio.run(main())
