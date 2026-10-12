"""Modal progress with an event loop: disk and pixel work run outside the UI thread."""
from PySide6.QtCore import QObject, QThreadPool, QEventLoop, Slot, Qt
from PySide6.QtWidgets import QProgressDialog
from .workers import Job
from .i18n import tr


class FileJobs(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.loop = None

    def run(self, operation, label):
        if self.loop is not None:
            raise RuntimeError("A file operation is already running")
        self.loop = QEventLoop()
        self.result, self.error = None, None
        progress = QProgressDialog(tr(label), "", 0, 0, self.parent())
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        job = Job(0, operation)
        job.signals.done.connect(self._finished)
        self.pool.start(job)
        self.loop.exec()
        self.loop = None
        progress.close()
        if self.error:
            raise self.error
        return self.result

    @Slot(int, object, object)
    def _finished(self, revision, result, error):
        self.result, self.error = result, error
        self.loop.quit()
