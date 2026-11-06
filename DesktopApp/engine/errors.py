"""Exceptions raised by the engine. UI, runners and the API all catch EngineError."""


class EngineError(Exception):
    """Base class for every error the engine raises on purpose."""


class ToolNotFound(EngineError):
    """engine.run() was asked for a tool that is not registered."""


class ParamError(EngineError, ValueError):
    """A parameter is unknown, has the wrong type, or is not an allowed choice."""


class ModelUnavailable(EngineError):
    """A model or its dependency is missing (e.g. 'pip install mediapipe')."""
