# First import the library
import pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2

class Image:
    def __init__(self, pipeline, config):
        self.pipeline = pipeline
        self.config = config

    def align_cams(self):
        config = self.config
        pipeline = self.pipeline

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")
            exit(0)

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        profile = pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: " , depth_scale)

        # We will be removing the background of objects more than
        #  clipping_distance_in_meters meters away
        clipping_distance_in_meters = 1 #1 meter
        clipping_distance = clipping_distance_in_meters / depth_scale

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        align = rs.align(align_to)
        return align, clipping_distance

    def get_Images(self, align, clipping_distance):
        # Get frameset of color and depth
        frames = self.pipeline.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return False

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Remove background - Set pixels further than clipping_distance to grey
        grey_color = 153
        depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #depth image is 1 channel, color is 3 channels
        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)
        return depth_image, bg_removed

    def find_Pen(self, images):
        #take the image frames
        frame = images #check this

        #BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        #define the purple color range in HSV
        lower_purp = np.array([110,50,50])
        upper_purp = np.array([130,255,255])

        #mask to only get purple colors
        mask = cv2.inRange(hsv, lower_purp, upper_purp)

        #bitwise mask and orig image
        res = cv2.bitwise_and(frame,frame, mask = mask)

        return res, mask

    def only_Pen(self, images, purple_images, mask):

        mask_inv = cv2.bitwise_not(mask)
        # res = cv2.bitwise_and(images,images, mask = mask_inv)
        # images = cv2.bitwise_and(pen_bitwise,pen_bitwise,mask = mask_inv)

        pen_image = cv2.bitwise_and(purple_images,purple_images,mask = mask_inv)

        return pen_image


    def take_image():
        return None #maybe use the key press to take images? and read them from a file?

    def render(self):
        try:
            while True:
                if(image.get_Images(align, clipping_distance) is False):
                    continue
                else:
                    depth_image, bg_removed = image.get_Images(align, clipping_distance)

                # Render images:
                #   depth align to color on left
                #   depth on right
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                images = np.hstack((bg_removed, depth_colormap)) #color map and depth map

                res, mask = self.find_Pen(images) #only show purple images (mask)
                images = cv2.bitwise_and(images, res, mask=mask)

                # images = self.only_Pen(images, purple_image, mask)
                # images = cv2.cvtColor(images, cv2.COLOR_BGR2GRAY)

                #showing the pop up window
                cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
                cv2.imshow('Align Example', images)
                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
        finally:
            self.pipeline.stop()


if  __name__ == "__main__":
    # # Create a pipeline
    pipeline = rs.pipeline()

    # Create a config and configure the pipeline to stream
    #  different resolutions of color and depth streams
    config = rs.config()
    image = Image(pipeline, config)
    align, clipping_distance = image.align_cams()
    image.render()
     