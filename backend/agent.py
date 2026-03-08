"""Backward-compatible agent export.

The original single-agent root_agent is replaced by the orchestrator agent team.
This file re-exports the orchestrator as root_agent so any existing imports still work.
"""

from agents.orchestrator import orchestrator_agent as root_agent

__all__ = ["root_agent"]
