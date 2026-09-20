from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
# The robot object is what you use to control the robot
robot = InterbotixManipulatorXS("px100", "arm", "gripper")


#move arm to start position
#open gripper
#measure the pen location
#turn at waist to align with pen
#adjust height so theyre at right level (later)
#move forward until it grabs pen

class Robot:
    def __init__(self):

        def move_robot():
            #release the gripper
            robot.gripper.grasp(0.01)

            # x,y,z = center
            #turn at waist to align with pen
            # robot.arm.set_single_joint_position("waist", 0.5, 1.0)
            robot.arm.set_single_joint_position("waist", 0.5, 1.0)

        def test_calibration():
            q_array = []
            coords = [(0.2, 0.1, 0.2), (0.2,-0.1,0.2), (0.2,0.1,0.1), (0.2,-0.1,0.1)] #[(x,y,z)]

            for coord in coords:
                #move robot to very left
                x,y,z = coord
                robot.arm.set_ee_pose_components(x=x, y=y, z=z)
                blocking = True #wait until its done
                q = robot.arm.get_ee_pose() #get the robot position this is Qi position 3x3 matrix
                print(q)
                q = tuple(q[:3,3]) #take x,y,z
                print(q)
                q_array.append(q)

        def test_arm():
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
    # robot.gripper.grasp(0.1)
    # test_arm()

    robot = Robot()

    robot.test_calibration()

    robot.arm.go_to_sleep_pose()

    robot_shutdown()