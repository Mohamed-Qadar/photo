"""Undo/redo history. Pure Python, no Qt.

Holds applied Command objects on an undo stack; undone commands move to a redo
stack. A `on_change` callback lets the UI refresh (titles, enabled states).
Consecutive commands may coalesce (e.g. slider drags) via Command.merge_with.
"""
from __future__ import annotations

from typing import Callable, Optional

from .commands import Command


class History:
    def __init__(self, on_change: Optional[Callable[[], None]] = None,
                 limit: int = 200) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self._limit = limit
        self.on_change = on_change

    def _changed(self) -> None:
        if self.on_change:
            self.on_change()

    def push(self, command: Command) -> None:
        """Execute a command and record it, coalescing with the previous if allowed."""
        command.do()
        if self._undo:
            prev = self._undo[-1]
            merged = prev.merge_with(command)
            if merged:
                # prev already reflects the new end-state after command.do();
                # keep prev, drop command as a separate step.
                self._redo.clear()
                self._changed()
                return
        self._undo.append(command)
        if len(self._undo) > self._limit:
            self._undo.pop(0)
        self._redo.clear()
        self._changed()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo_label(self) -> str:
        return self._undo[-1].label if self._undo else ""

    def redo_label(self) -> str:
        return self._redo[-1].label if self._redo else ""

    def undo(self) -> None:
        if not self._undo:
            return
        cmd = self._undo.pop()
        cmd.undo()
        self._redo.append(cmd)
        self._changed()

    def redo(self) -> None:
        if not self._redo:
            return
        cmd = self._redo.pop()
        cmd.do()
        self._undo.append(cmd)
        self._changed()

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._changed()
