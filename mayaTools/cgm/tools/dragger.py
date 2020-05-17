from cgm.core import cgm_Meta as cgmMeta
from cgm.core.lib import transform_utils as TRANS
from cgm.core.lib import math_utils as MATH
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core.lib import snap_utils as SNAP

import maya.cmds as mc
import maya.mel as mel

class Dragger(object):
    def __init__(self, obj = None, aimFwd = 'z+', aimUp = 'y+', damp = 7.0, offset=100, velocityScalar=1, velocityDamp=6):
        self.obj = obj

        if obj is None:
            self.obj = cgmMeta.asMeta( mc.ls(sl=True)[0] )

        self.aimFwd = VALID.simpleAxis(aimFwd)
        self.aimUp = VALID.simpleAxis(aimUp)

        self.damp = damp
        self.offset = offset
        self.velocityScalar = velocityScalar
        self.velocityDamp = velocityDamp

        self.dir = self.obj.getTransformDirection(self.aimFwd.p_vector)*self.offset
        self.aimTargetPos = self.obj.p_position + self.dir

        self.velocity = MATH.Vector3.zero()
        self._prevPos = VALID.euclidVector3Arg(self.obj.p_position)

        self._startPos = self._prevPos

    def bake(self, startTime=None, endTime=None):
        startTime = int(mc.playbackOptions(q=True, min=True))
        endTime = int(mc.playbackOptions(q=True, max=True))

        fps = mel.eval('currentTimeUnitToFPS')
        
        fixedDeltaTime = 1.0/fps

        for i in range(startTime, endTime+1):
            mc.currentTime(i)

            self.update(fixedDeltaTime)

        self.velocity = MATH.Vector3.zero()
        self._prevPos = self._startPos
        self.aimTargetPos = self._startPos + self.dir

    def update(self, deltaTime=.04):
        #dir = self.obj.getTransformDirection(self.aimFwd.p_vector)

        self.velocity = MATH.Vector3.Lerp(self.velocity, VALID.euclidVector3Arg(self.obj.p_position) - self._prevPos, deltaTime * self.velocityDamp)
        self._prevPos = VALID.euclidVector3Arg(self.obj.p_position)

        wantedTargetPos = ((VALID.euclidVector3Arg(self.obj.p_position) + self.dir + self.velocity * self.velocityScalar) - self.obj.p_position).normalized()*self.offset + self.obj.p_position
        #wantedUp = self.obj.getTransformDirection(self.aimUp.p_vector)

        self.aimTargetPos = (MATH.Vector3.Lerp(self.aimTargetPos, wantedTargetPos, deltaTime*self.damp) - self.obj.p_position).normalized()*self.offset + self.obj.p_position

        SNAP.aim_atPoint(obj=self.obj, position=self.aimTargetPos, aimAxis=self.aimFwd.p_string, upAxis=self.aimUp.p_string)

        mc.setKeyframe(self.obj.mNode, at='rotate')







