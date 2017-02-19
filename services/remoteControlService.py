from pyupnp.event import EventProperty
from pyupnp.services import Service, ServiceActionArgument,\
    register_action, ServiceStateVariable

class RemoteControlService(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:RemoteControlService:1"
    serviceId = "urn:upnp-org:serviceId:RemoteControlService"

    subscription_timeout_range = (None, None)

    stateVariables = [
        # Arguments
        # ServiceStateVariable('button',                  'string', sendEvents=True),
        # ServiceStateVariable('beginRecognitionControl', 'ui4', sendEvents=True),
        ServiceStateVariable('tvCommandControl',      'string', sendEvents=True),
            ]

    actions = {
        # 'Click': [
        #     ServiceActionArgument('button',         'in',   'button'),
        # ],
        # 'SetTvCommand': [
        #     ServiceActionArgument('command',      'string',   'tvCommandControl'),
        # ],
    }

    # button                  = EventProperty('button')
    # beginRecognitionControl = EventProperty('beginRecognitionControl')
    tvCommandControl      = EventProperty('tvCommandControl')

    # @register_action('Click')
    # def click(self,button):
    #     raise NotImplementedError()

    # @register_action('SetTvCommand')
    # def setTvCommand(self,command):
    #     raise NotImplementedError()