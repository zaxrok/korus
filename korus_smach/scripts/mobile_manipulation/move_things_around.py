#!/usr/bin/env python

'''
Move Things Around App

App for picking objects up from a table in one place and placing them on a table in another place
'''

import math
import roslib; roslib.load_manifest('korus_smach')
import rospy
import smach
from smach import StateMachine
import smach_ros
from smach_ros import SimpleActionState
#import smach_ros
#from smach_ros import ActionServerWrapper
import tf
from tf import TransformListener
import geometry_msgs.msg as geometry_msgs
#import control_msgs

from korus_smach.state_machines import find_object_sm, pick_object_sm, place_object_sm

import move_base_msgs.msg as move_base_msgs


class Prepare(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                             outcomes=['prepared'],
                             input_keys=[],
                             output_keys=[])
    def execute(self, userdata):
        return 'prepared'
    
class PreparePickObject(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                             outcomes=['prepared',
                                       'error'],
                             input_keys=['recognised_objects',
                                         'recognised_object_names',
                                         'pick_object_pose',
                                         'pick_object_name',
                                         'tf_listener'],
                             output_keys=['pick_object_pose',
                                         'pick_object_name',
                                         'tf_listener'])
    def execute(self, userdata):
        max_confidence = 0.0
        object_index = 0
        if len(userdata.recognised_objects.objects) is not len(userdata.recognised_object_names):
            rospy.logerr("Number of recognised objects does not match object names!")
            return 'error'
        for object in userdata.recognised_objects.objects:
            if object.confidence > max_confidence:
                max_confidence = object.confidence
                object_index = userdata.recognised_objects.objects.index(object)
                
        userdata.pick_object_name = userdata.recognised_object_names[object_index]
        userdata.pick_object_pose = geometry_msgs.PoseStamped()
        userdata.pick_object_pose.header = userdata.recognised_objects.objects[object_index].pose.header
        userdata.pick_object_pose.pose = userdata.recognised_objects.objects[object_index].pose.pose.pose
        rospy.loginfo("Object '" + str(userdata.pick_object_name) + "' has been selected among all recognised objects")
        rospy.loginfo("Object's pose:")
        rospy.loginfo(userdata.pick_object_pose)
        
        angle = math.atan2(userdata.pick_object_pose.pose.position.y, userdata.pick_object_pose.pose.position.x)
        dist = math.sqrt(math.pow(userdata.pick_object_pose.pose.position.x, 2) + math.pow(userdata.pick_object_pose.pose.position.y, 2))
        userdata.pick_object_pose.pose.position.x = (dist - 0.18) * math.cos(angle)
        userdata.pick_object_pose.pose.position.y = (dist - 0.18) * math.sin(angle)
        userdata.pick_object_pose.pose.position.z = userdata.pick_object_pose.pose.position.z + 0.15
        yaw = angle
        roll = math.pi / 2
        pitch = 0.0
        quat = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
        userdata.pick_object_pose.pose.orientation = geometry_msgs.Quaternion(*quat)
        rospy.loginfo("Object's pose after adaption:")
        rospy.loginfo(userdata.pick_object_pose)
        
        
        return 'prepared'

class Finalise(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                             outcomes=['finalised'],
                             input_keys=[],
                             output_keys=[])
        
    def execute(self, userdata):
        return 'finalised'


def main():
    rospy.init_node('move_things_around')
    
    sm = StateMachine(outcomes=['success',
                                'aborted',
                                'preempted'])
    with sm:
        ''' table poses '''
        sm.userdata.pose_table_a = geometry_msgs.PoseStamped()
        sm.userdata.pose_table_a.header.stamp = rospy.Time.now()
        sm.userdata.pose_table_a.header.frame_id = "/map"
        sm.userdata.pose_table_a.pose.position.x = -0.074
        sm.userdata.pose_table_a.pose.position.y = 1.202
        sm.userdata.pose_table_a.pose.orientation.x = 0.0
        sm.userdata.pose_table_a.pose.orientation.y = 0.0
        sm.userdata.pose_table_a.pose.orientation.z = 0.995
        sm.userdata.pose_table_a.pose.orientation.w = 0.098
        sm.userdata.pose_table_b = geometry_msgs.PoseStamped()
        sm.userdata.pose_table_b.header = sm.userdata.pose_table_a.header
        sm.userdata.pose_table_b.pose.position.x = 3.400
        sm.userdata.pose_table_b.pose.position.y = 0.680
        sm.userdata.pose_table_b.pose.orientation.x = 0.0
        sm.userdata.pose_table_b.pose.orientation.y = 0.0
        sm.userdata.pose_table_b.pose.orientation.z = 0.031
        sm.userdata.pose_table_b.pose.orientation.w = 1.0
        ''' Korus base pose '''
        sm.userdata.base_position = geometry_msgs.PoseStamped()
        ''' tabletop poses '''
        sm.userdata.pose_tabletop_a = geometry_msgs.PoseStamped()
        sm.userdata.pose_tabletop_a.header.stamp = rospy.Time.now()
        sm.userdata.pose_tabletop_a.header.frame_id = "/base_footprint"
        sm.userdata.pose_tabletop_a.pose.position.x = 0.1
        sm.userdata.pose_tabletop_a.pose.position.y = 0.0
        sm.userdata.pose_tabletop_a.pose.position.z = 0.0
        sm.userdata.pose_tabletop_a.pose.orientation.x = 0.0
        sm.userdata.pose_tabletop_a.pose.orientation.y = 0.0
        sm.userdata.pose_tabletop_a.pose.orientation.z = 0.0
        sm.userdata.pose_tabletop_a.pose.orientation.w = 1.0
        sm.userdata.pose_tabletop_b = geometry_msgs.PoseStamped()
        sm.userdata.pose_tabletop_b.header = sm.userdata.pose_tabletop_a.header
        sm.userdata.pose_tabletop_b.pose.position.x = 0.7
        sm.userdata.pose_tabletop_b.pose.position.y = 0.0
        sm.userdata.pose_tabletop_b.pose.position.z = 0.8
        sm.userdata.pose_tabletop_b.pose.orientation.x = 0.0
        sm.userdata.pose_tabletop_b.pose.orientation.y = 0.0
        sm.userdata.pose_tabletop_b.pose.orientation.z = 0.0
        sm.userdata.pose_tabletop_b.pose.orientation.w = 1.0
        ''' find object'''
        sm.userdata.look_around_false = False
        sm.userdata.min_confidence = 0.8
        sm.userdata.object_names = list()
        sm.userdata.tf_listener = tf.TransformListener()
        
        smach.StateMachine.add('Prepare',
                               Prepare(),
                               remapping={},
                               transitions={'prepared':'FindObject'})
        
#        smach.StateMachine.add('MoveToTableA',
#                               SimpleActionState('move_base',
#                                                 move_base_msgs.MoveBaseAction,
#                                                 goal_slots=['target_pose'],
#                                                 result_slots=[]),
#                               remapping={'target_pose':'pose_table_a',
#                                          'base_position':'base_position'},
#                               transitions={'succeeded':'FindObject',
#                                            'aborted':'aborted',
#                                            'preempted':'preempted'})
        
        sm_find_object = find_object_sm.createSM()
        smach.StateMachine.add('FindObject',
                               sm_find_object,
                               remapping={'table_pose':'pose_tabletop_b',
                                          'look_around':'look_around_false',
                                          'min_confidence':'min_confidence',
                                          'recognised_objects':'recognised_objects',
                                          'object_names':'object_names',
                                          'object_pose':'pick_object_pose',
                                          'error_message':'error_message',
                                          'error_code':'error_code',
                                          'tf_listener':'tf_listener'},
                               transitions={'object_found':'PreparePickObject',
                                            'no_objects_found':'Finalise',
                                            'aborted':'aborted',
                                            'preempted':'preempted'})
        
        smach.StateMachine.add('PreparePickObject',
                               PreparePickObject(),
                               remapping={'recognised_objects':'recognised_objects',
                                          'recognised_object_names':'object_names',
                                          'pick_object_pose':'pick_object_pose',
                                          'pick_object_name':'pick_object_name',
                                          'tf_listener':'tf_listener'},
                               transitions={'prepared':'PickObject',
                                            'error':'aborted'})
        
        sm_pick_object = pick_object_sm.createSM()
        smach.StateMachine.add('PickObject',
                               sm_pick_object,
                               remapping={'object_pose':'pick_object_pose',
                                          'object_name':'pick_object_name'},
                               transitions={'picked':'Finalise',
                                            'pick_failed':'Finalise',
                                            'error':'aborted',
                                            'preempted':'preempted'})
        
#        smach.StateMachine.add('MoveToTableB',
#                               SimpleActionState('move_base',
#                                                 move_base_msgs.MoveBaseAction,
#                                                 goal_slots=['target_pose'],
#                                                 result_slots=[]),
#                               remapping={'target_pose':'pose_table_b',
#                                          'base_position':'base_position'},
#                               transitions={'succeeded':'MoveToTableA',
#                                            'aborted':'aborted',
#                                            'preempted':'preempted'})
#        
#        sm_place = place_sm.createSM()
#        smach.StateMachine.add('PlaceObject',
#                               sm_place,
#                               remapping={'place_pose':'place_object_pose'},
#                               transitions={'object_placed':'Finalise',
#                                            'place_failed':'MoveToTableB',
#                                            'aborted':'aborted',
#                                            'preempted':'preempted'})
        
        smach.StateMachine.add('Finalise',
                               Finalise(),
                               remapping={},
                               transitions={'finalised':'success'})
    
    sm.execute()


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
    