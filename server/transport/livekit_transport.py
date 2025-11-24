from pipecat.transports.services.livekit import LiveKitTransport, LiveKitParams

# We re-export the Pipecat LiveKit transport here.
# If we needed custom audio handling or frame manipulation before sending to LiveKit, 
# we would subclass it here.

class CustomLiveKitTransport(LiveKitTransport):
    """
    Custom wrapper around Pipecat's LiveKitTransport.
    Allows for future extension of audio frame handling or event hooks.
    """
    pass

