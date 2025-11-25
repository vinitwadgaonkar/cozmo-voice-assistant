"""LiveKit JWT token generation for agent authentication."""

from livekit import api as lk_api
from .config import VoiceAgentConfig


def create_access_token(cfg: VoiceAgentConfig, room_name: str, identity: str) -> str:
    """
    Create a JWT token that lets the agent join the given LiveKit room.
    
    This uses the actual LiveKit AccessToken + VideoGrants APIs to generate
    a valid JWT that authorizes the agent to publish and subscribe in the room.
    
    Args:
        cfg: Voice agent configuration with LiveKit credentials
        room_name: Name of the LiveKit room to join
        identity: Participant identity for the agent
        
    Returns:
        str: JWT token string
    """
    grants = lk_api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
    )

    token = lk_api.AccessToken(
        api_key=cfg.livekit.api_key,
        api_secret=cfg.livekit.api_secret,
        grants=grants,
        identity=identity,
    )

    return token.to_jwt()

