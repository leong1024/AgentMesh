"""Build AgentCard manifests for A2A servers."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(
    *,
    name: str,
    description: str,
    skill_id: str,
    skill_name: str,
    public_url: str,
    version: str = "0.1.0",
) -> AgentCard:
    """Standard JSON-RPC card for localhost or compose URLs."""
    base = public_url.rstrip("/")
    return AgentCard(
        name=name,
        description=description,
        url=base,
        version=version,
        protocol_version="0.3.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=[
            AgentSkill(
                id=skill_id,
                name=skill_name,
                description=skill_name,
                tags=["agentmesh", skill_id],
            )
        ],
        supports_authenticated_extended_card=False,
    )
