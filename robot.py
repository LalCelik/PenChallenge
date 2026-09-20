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

    def move_robot(self):
        #release the gripper
        robot.gripper.grasp(0.01)

        # x,y,z = center
        #turn at waist to align with pen
        # robot.arm.set_single_joint_position("waist", 0.5, 1.0)
        robot.arm.set_single_joint_position("waist", 0.5, 1.0)

    def test_calibration(self):
        pipeline = rs.pipeline()
        config = rs.config()

        camera = Image(pipeline, config)
        align, clipping_distance = camera.align_cams()

        try:
            q_array = []
            coord_array = []
            coords = [(0.2, 0.1, 0.2),
                      (0.2,-0.1,0.2),
                      (0.2,0.1,0.1),
                      (0.2,-0.1,0.1)] #[(x,y,z)]

            for coord in coords:
                #move robot to very left
                x,y,z = coord
                robot.arm.set_ee_pose_components(x=x, y=y, z=z)
                blocking = True #wait until its done
                q = robot.arm.get_ee_pose() #get the robot position this is Qi position 3x3 matrix
                # print(q)
                q = tuple(q[:3,3]) #take x,y,z
                # print(q)
                q_array.append(q)
                pen_coord = camera.get_coords_once(align,clipping_distance) #Pi
                # print("Coordinates:", pen_coord)
                coord_array.append(pen_coord) 

            print(len(q_array))
            print(len(coord_array))
            print(coord_array)

            rotation, rmsd = Rotation.align_vectors(q_array, coord_array)
            r = rotation.as_matrix()
            print("Rotation Matrix:", r)
            t = self.find_t(coord_array, q_array, r)


            robot.arm.go_to_sleep_pose()
            time.sleep(4)



            #going to the pen
            new_pen = camera.get_coords_once(align,clipping_distance)
            q_new = r @ new_pen + t
            x_n, y_n, z_n = q_new
            robot.arm.set_ee_pose_components(x_n, y_n, z_n)


        finally:
            pipeline.stop

    def find_t(self, p_list, q_list, r):
        p_avg = np.mean(np.array(p_list), axis=0) / len(p_list)
        q_avg = np.mean(np.array(q_list), axis=0) / len(q_list)
        t = q_avg - r @ p_avg
        return t

    def test_arm(self):
        mode = 'h'
        # Let the user select the position
        while mode != 'q':
            mode=input("[h]ome, [s]leep, [q]uit ")
            if mode == "h":
                robot.arm.go_to_home_pose()
            elif mode == "s":
                robot.arm.go_to_sleep_pose()
            elif mode == "r":
                robot.gripper.release()
            elif mode == "g":
                robot.gripper.grasp()

if  __name__ == "__main__":
    robot_startup()
    robot.arm.go_to_sleep_pose()

    # robot.gripper.release()
    # robot.gripper.grasp(0.2)
    # test_arm()

    # pipeline = rs.pipeline()
    # config = rs.config()

    # camera = Image(pipeline, config)
    # align, clipping_distance = camera.align_cams()

    # camera.render(align,clipping_distance)  # press q or Esc to leave the camera loop


    robot_class = Robot()
    robot_class.test_calibration()

    # robot.arm.go_to_sleep_pose()

    # robot_shutdown()