"""Automations and scheduling for KOMPAGNON."""

from .scheduler import CompagnonScheduler, get_scheduler, start_scheduler, stop_scheduler
from .email_templates import TEMPLATES, get_template, render_template

__all__ = [
    "CompagnonScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    "TEMPLATES",
    "get_template",
    "render_template",
]
