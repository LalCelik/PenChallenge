from rclpy.impl.rcutils_logger import RcutilsLogger
if not hasattr(RcutilsLogger, "warn"):
    RcutilsLogger.warn = RcutilsLogger.warning

from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
# The robot object is what you use to control the robot
robot = InterbotixManipulatorXS("px100", "arm", "gripper")
from scipy.spatial.transform import Rotation


import pyrealsense2 as rs
from image import Image
import numpy as np
import time


#move arm to start position
#open gripper
#measure the pen location
#turn at waist to align with pen
#adjust height so theyre at right level (later)
#move forward until it grabs pen

class Robot:
    def __init__(self):
        pass

    def test_calibration(self):
        pipeline = rs.pipeline()
        config = rs.config()

        camera = Image(pipeline, config)
        align, clipping_distance = camera.align_cams()

        try:
            q_array = []
            coord_array = []
            coords = [(0.2, 0.1, 0.2),
                      (0.2, 0.2, 0.1),
                      (0.2, 0.2, 0.2),
                      (0.2,-0.1,0.2),
                      (0.2,0.1,0.1),
                      (0.2,-0.1,0.1)] #[(x,y,z)]

            for coord in coords:
                #move robot to very left
                x,y,z = coord
                i, success = robot.arm.set_ee_pose_components(x=x, y=y, z=z)
                if not success:
                    print("Pen is in invalid position")
                    continue
                blocking = True #wait until its done
                q = robot.arm.get_ee_pose() #get the robot position this is Qi position 3x3 matrix
                # print("Robot Position:", q)
                q = tuple(q[:3,3]) #take x,y,z
                # print("Robot Position:", q)
                if(q is None):
                    continue

                q_array.append(q)
                pen_coord = camera.get_coords_once(align,clipping_distance) #Pi
                if pen_coord is None:
                    print("Pen not detected, skipping this sample")
                    continue 
                coord_array.append(pen_coord)

            print(coord_array)

            r = self.find_r(coord_array, q_array)
            print("Rotation Matrix:", r)
            t = self.find_t(coord_array, q_array, r)

            self.grab_pen(camera, align, clipping_distance, r, t)

            pipeline.stop()
        finally:
            pipeline.stop()

    def calibration(self, camera, align, clipping_distance):
        q_array = []
        coord_array = []
        coords = [(0.2, 0.1, 0.2),
                    (0.2, 0.2, 0.1),
                    (0.2, 0.2, 0.2),
                    (0.2,-0.1,0.2),
                    (0.2,0.1,0.1),
                    (0.2,-0.1,0.1)] #[(x,y,z)]

        for coord in coords:
            #move robot to very left
            x,y,z = coord
            i, success = robot.arm.set_ee_pose_components(x=x, y=y, z=z)
            if not success:
                print("Pen is in invalid position")
                continue
            blocking = True #wait until its done
            q = robot.arm.get_ee_pose() #get the robot position this is Qi position 3x3 matrix
            # print("Robot Position:", q)
            q = tuple(q[:3,3]) #take x,y,z
            # print("Robot Position:", q)
            if(q is None):
                continue

            q_array.append(q)
            pen_coord = camera.get_coords_once(align,clipping_distance) #Pi
            if pen_coord is None:
                print("Pen not detected, skipping this sample")
                continue 
            coord_array.append(pen_coord)

        print(coord_array)

        r = self.find_r(coord_array, q_array)
        print("Rotation Matrix:", r)
        t = self.find_t(coord_array, q_array, r)
        return r,t


    def grab_pen(self, camera, align, clipping_distance, r, t):

        robot.arm.go_to_sleep_pose()
        robot.gripper.release()

        #going to the pen
        while True:
            time.sleep(2)
            new_pen = camera.get_coords_once(align,clipping_distance)
            print(new_pen)
            if(new_pen is None):
                print("No pen detected")
                continue
            q_new = r @ new_pen + t

            x_n, y_n, z_n = q_new

            robot.arm.set_ee_pose_components(x_n, y_n, z_n)
            robot.gripper.grasp()
            break



    def find_r(self, p_list, q_list):
        p_avg = np.mean(np.array(p_list), axis=0)
        q_avg = np.mean(np.array(q_list), axis=0)
        p_cen = []
        q_cen = []

        for i in range(len(p_list)):
            p_c = np.array(p_list[i]) - p_avg
            q_c = np.array(q_list[i]) - q_avg
            p_cen.append(p_c)
            q_cen.append(q_c)
        
        rotation, rmsd = Rotation.align_vectors(p_cen, q_cen)
        r = rotation.as_matrix()
        return r


    def find_t(self, p_list, q_list, r):
        p_avg = np.mean(np.array(p_list), axis=0)
        q_avg = np.mean(np.array(q_list), axis=0)
        t = q_avg - r @ p_avg
        return t

    def test_arm(self):
        mode = 'h'
        # Let the user select the position
        calibrated = False
        while mode != 'q':
            robot_class = Robot()
            pipeline = rs.pipeline()
            config = rs.config()

            camera = Image(pipeline, config)
            align, clipping_distance = camera.align_cams()
            try:

                mode=input("[c]alibrate, [g]rab pen, [q]uit ")
                if mode == "c":
                    calibrated = True
                    r, t = robot_class.calibration( camera, align, clipping_distance)
                elif mode == "g":
                    if(calibrated):
                        robot_class.grab_pen( camera, align, clipping_distance, r, t)
                    else:
                        print("Robot is not calibrated")
                    
            finally:
                pipeline.stop()
                

if  __name__ == "__main__":
    robot_startup()
    robot.arm.go_to_sleep_pose()

    robot.gripper.release()
    robot.gripper.grasp(0.01)
    time.sleep(2)

    robot_class = Robot()
    # robot_class.move_robot()
    # robot_class.test_calibration()

    robot_class.test_arm()

    robot.arm.go_to_sleep_pose()

    robot_shutdown()