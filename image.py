# First import the library
import pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2
from matplotlib import pyplot as plt

class Image:
    def __init__(self, pipeline, config):
        self.pipeline = pipeline
        self.config = config

    def align_cams(self):
        # config = self.config
        # pipeline = self.pipeline

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
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

        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        profile = self.pipeline.start(self.config)
        self.config = profile

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
        # print(frames.get_depth_frame().get_distance(2,3))

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # print(aligned_depth_frame.get_distance(2,3))

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return False

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Remove background - Set pixels further than clipping_distance to grey
        grey_color = 153
        depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #depth image is 1 channel, color is 3 channels
        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)
        return depth_image, bg_removed, aligned_depth_frame

    def find_Pen(self, images):
        #BGR to HSV
        hsv = cv2.cvtColor(images, cv2.COLOR_BGR2HSV)

        #define the purple color range in HSV
        lower_purp = np.array([110,50,50])
        upper_purp = np.array([130,255,255])

        #mask to only get purple colors
        mask = cv2.inRange(hsv, lower_purp, upper_purp)

        #bitwise mask and orig image
        res = cv2.bitwise_and(images,images, mask = mask)
        return res, mask

    #join the points that have the same color or intensity
    def contour(self, mask):
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        approx = None
        center = None
        ellipse_contour = None

        if(contours):
            #merge contour points
            #so that parts of the pen aren't separated
            all_points = np.concatenate(contours, axis=0) #put all the points in one list
            contour = cv2.convexHull(all_points) #use convex hull to get the contour of the outer sides

            if(len(contour) >= 5):
                ellipse = cv2.fitEllipse(contour)
                mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) #elipse can't take in gray mask
                ellipse_contour = cv2.ellipse(mask_bgr, ellipse,(0,255,0),2) 
                (xc, yc), (axes_width, axes_height), angle = ellipse
                center_x = int(xc) 
                center_y = int(yc)
                center = (center_x, center_y)
        return contours, ellipse_contour, approx, center

#pixel to coords in meters
    def find_coords(self,center, depth_image):
        # cfg = pipeline.start(self.config)
        profile = self.config.get_stream(rs.stream.color)

        if(profile is not None and center is not None):
            intr = profile.as_video_stream_profile().get_intrinsics()
            px, py = center
            depth_in_meters = depth_image.get_distance(px,py) #get back to this erroring when off screen
            x,y,z = rs.rs2_deproject_pixel_to_point(intr, [px, py], depth_in_meters)

        return x,y,z


    def take_image():
        return None #maybe use the key press to take images? and read them from a file?

    def render(self):
        try:
            while True:
                if(image.get_Images(align, clipping_distance) is False):
                    continue
                else:
                    depth_image, bg_removed, aligned_depth_frame = image.get_Images(align, clipping_distance)

                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
    
                color_blurred = cv2.blur(bg_removed, (5,5))
                found, mask = self.find_Pen(color_blurred) #only show purple images (mask)
                contours, ellipse_contour, approx, center = self.contour(mask)

                if(center is not None):
                    cv2.circle(found, center, 40, (0,255,0), 40)
                    cv2.imshow("Ellipse", ellipse_contour)
                    
                    x,y,z = self.find_coords(center, aligned_depth_frame)
                    print((x,y,z))

                contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                cv2.drawContours(found, contours, -1, (0,255,0), 3)
                cv2.drawContours(found, approx, -1, (0,255,0), 3)

                images = np.hstack((found, depth_colormap)) #color map and depth maps

                cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
                cv2.imshow('Align Example', images)

                # cv2.imshow('Align Example', images)
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
     