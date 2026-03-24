"""Matplotlib canvas widget for map and trajectory visualization."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class CanvasWidget(QWidget):
    """Interactive plotting area with click-to-set points."""

    point_clicked = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.figure.set_facecolor("#f7f8fb")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self._connect_events()

    def _connect_events(self) -> None:
        self.canvas.mpl_connect("button_press_event", self._on_click)

    def _on_click(self, event) -> None:
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        self.point_clicked.emit(int(round(event.xdata)), int(round(event.ydata)))

    def draw_scene(
        self,
        grid,
        start=None,
        goal=None,
        path=None,
        rrt_edges=None,
        show_rrt_tree: bool = True,
    ) -> None:
        """Render map and route elements."""
        self.ax.clear()
        self.ax.set_facecolor("#f2f4f8")
        self.ax.imshow(grid, cmap="Greys", origin="upper", alpha=0.95)

        if rrt_edges and show_rrt_tree:
            for a, b in rrt_edges:
                self.ax.plot([a[0], b[0]], [a[1], b[1]], color="#95a3b3", linewidth=0.8, alpha=0.45)

        if path and len(path) > 1:
            xs = [p[0] for p in path]
            ys = [p[1] for p in path]
            self.ax.plot(xs, ys, color="#1f6feb", linewidth=2.8, alpha=0.98, solid_capstyle="round")

        if start:
            self.ax.scatter(start[0], start[1], c="#1f883d", s=90, label="Start", edgecolors="white", linewidths=1.2, zorder=5)
        if goal:
            self.ax.scatter(goal[0], goal[1], c="#cf222e", s=90, label="Goal", edgecolors="white", linewidths=1.2, zorder=5)

        self.ax.set_title("Карта и траектория", fontsize=12, fontweight="bold", color="#202938")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.grid(color="#c5cfdb", linewidth=0.55, alpha=0.35)
        if start or goal:
            leg = self.ax.legend(loc="upper right", frameon=True, fontsize=9)
            leg.get_frame().set_facecolor("#ffffff")
            leg.get_frame().set_edgecolor("#d8dee7")
            leg.get_frame().set_alpha(0.92)
        self.ax.set_aspect("equal", adjustable="box")
        self.figure.tight_layout()
        self.canvas.draw_idle()
