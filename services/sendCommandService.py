from pyupnp.event import EventProperty
from pyupnp.services import Service, ServiceActionArgument,\
    register_action, ServiceStateVariable

class SendCommandService(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:SendCommandService:1"
    serviceId = "urn:upnp-org:serviceId:SendCommandService"

    subscription_timeout_range = (1800, 2000)

    stateVariables = [
        # Arguments
        ServiceStateVariable('sentTvCommand',               'string')
            ]

    actions = {
        'SendCommand': [
            ServiceActionArgument('sentTvCommand',           'in',   'sentTvCommand'),
        ],
    }
    
    @register_action('SendCommand')
    def sendCommand(self,sentTvCommand):
        raise NotImplementedError()
