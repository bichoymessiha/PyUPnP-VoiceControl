from pyupnp.event import EventProperty
from pyupnp.services import Service, ServiceActionArgument,\
    register_action, ServiceStateVariable

class SpeechToTextService(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:SpeechToTextService:1"
    serviceId = "urn:upnp-org:serviceId:SpeechToTextService"

    subscription_timeout_range = (None, None)

    stateVariables = [
        # Arguments
        ServiceStateVariable('transcribedText',         'string', sendEvents=True),
            ]

    actions = {
        'BeginRecognition': [
        ],
    }

    transcribedText = EventProperty('transcribedText')

    @register_action('BeginRecognition')
    def beginRecognition(self):
        raise NotImplementedError()
