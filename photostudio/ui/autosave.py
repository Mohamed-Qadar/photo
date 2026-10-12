"""Periodic atomic recovery writes on a worker, isolated per editor instance."""
import uuid
from PySide6.QtCore import QObject, QTimer, QThreadPool, Signal, Slot
from ..core.recovery import data_root
from ..core.project_io import save_project
from .workers import snapshot, Job


class Autosave(QObject):
    failed = Signal(str)
    saved = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        root = data_root() / "recovery"
        root.mkdir(exist_ok=True)
        self.path = root / f"{uuid.uuid4().hex}.pstudio"
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.running = False
        self.last_revision = None
        self._active_path = None
        self.stopping = False
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self.write)
        self.timer.start()
        controller.document_opened.connect(self.clear)

    def write(self):
        c = self.controller
        if self.running or c.interaction_active or not c.document or not c.is_dirty or c._revision == self.last_revision:
            return
        self.running = True
        revision = c._revision
        source = snapshot(c.document)
        target = self.path
        self._active_path = target
        job = Job(revision, lambda: save_project(source, target))
        job.signals.done.connect(self._finished)
        self.pool.start(job)

    @Slot(int, object, object)
    def _finished(self, revision, result, error):
        self.running = False
        if self.stopping or self._active_path != self.path:
            if self._active_path:
                self._active_path.unlink(missing_ok=True)
            self._active_path = None
            return
        if error:
            self.failed.emit(str(error))
        else:
            self.last_revision = revision if revision == self.controller._revision else None
            self.saved.emit()

    def clear(self):
        if self.running:
            # The completion slot removes the previous document's recovery file.
            # Switching documents never waits for compression on the UI thread.
            self.path = self.path.parent / f"{uuid.uuid4().hex}.pstudio"
        else:
            self.path.unlink(missing_ok=True)
        self.last_revision = None

    def shutdown(self):
        self.timer.stop()
        self.stopping = True
        self.pool.waitForDone()
        self.path.unlink(missing_ok=True)
        if self._active_path:
            self._active_path.unlink(missing_ok=True)
