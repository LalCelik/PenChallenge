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

def move_robot():
    #release the gripper
    robot.gripper.grasp(0.01)

    # x,y,z = center
    #turn at waist to align with pen
    # robot.arm.set_single_joint_position("waist", 0.5, 1.0)
    robot.arm.set_single_joint_position("waist", 0.5, 1.0)

def test_calibration():
    #move robot to very left 
    #get location
    robot.arm.set_single_joint_position("waist", 0.5, 1.0)

    positions = [(0,0)]
    for (px_, py_, pz_) in positions:
        # move robot to that position 
        # robot.arm.set_ee_pose_components(x=px_, y=py_, z=pz_, moving_time=2.0, blocking=True)
        # time.sleep(settle_time)

        #robots current position
        # T = robot.arm.get_ee_pose()
        # Q = tuple(T[:3, 3])


    #move robot to very right
    #get location
    robot.arm.set_single_joint_position("waist", 0.5, 1.0)






if  __name__ == "__main__":
    robot_startup()
    robot.arm.go_to_sleep_pose()
    mode = 'h'
    # # Let the user select the position
    # while mode != 'q':
    #     mode=input("[h]ome, [s]leep, [q]uit ")
    #     if mode == "h":
    #         robot.arm.go_to_home_pose()
    #     elif mode == "s":
    #         robot.arm.go_to_sleep_pose()
    #     elif mode == "r":
    #         robot.gripper.release()
    #     elif mode == "g":
    #         robot.gripper.grasp()

    # move_robot()
    # robot.gripper.release()
    # robot.gripper.grasp()


    robot_shutdown()