from livekit.agents import cli, WorkerOptions
from agent.app.run_agent import entrypoint

if __name__ == "__main__":
    # Wrapper to run the worker
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

