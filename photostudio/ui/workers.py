"""Bounded background rendering. Workers own snapshots; only signals touch the UI."""
from __future__ import annotations

import copy
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from ..core.pipeline import composite


def snapshot(document):
    # Pixel arrays are replaced, never edited in place by commands. Share those
    # buffers; copy mutable metadata so UI edits cannot race a render.
    doc = copy.copy(document)
    doc.layers = []
    for layer in document.layers:
        item = copy.copy(layer)
        item.spec = copy.deepcopy(layer.spec)
        item.adjustments = dict(layer.adjustments)
        doc.layers.append(item)
    return doc


class JobSignals(QObject):
    done = Signal(int, object, object)


class Job(QRunnable):
    def __init__(self, revision, operation):
        super().__init__()
        self.revision, self.operation = revision, operation
        self.signals = JobSignals()

    @Slot()
    def run(self):
        try:
            self.signals.done.emit(self.revision, self.operation(), None)
        except Exception as exc:
            self.signals.done.emit(self.revision, None, exc)


class RenderQueue(QObject):
    ready = Signal(object)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.revision = 0
        self.pending = None
        self.running = False

    def request(self, document, use_adjustments=True):
        self.revision += 1
        self.pending = (self.revision, snapshot(document), use_adjustments)
        if not self.running:
            self._start()

    def _start(self):
        revision, doc, adjusted = self.pending
        self.pending = None
        self.running = True
        job = Job(revision, lambda: composite(doc, use_adjustments=adjusted))
        job.signals.done.connect(self._finished)
        self.pool.start(job)

    @Slot(int, object, object)
    def _finished(self, revision, result, error):
        self.running = False
        if revision == self.revision:
            if error is not None:
                self.failed.emit(str(error))
            else:
                self.ready.emit(result)
        if self.pending is not None:
            self._start()

    def invalidate(self):
        self.revision += 1
        self.pending = None
