import os
import sys

if getattr(sys, "frozen", False):

    meipass = getattr(sys, "_MEIPASS", "")

    plugin_path = os.path.join(
        meipass,
        "_internal",
        "PySide6",
        "plugins",
    )

    if os.path.isdir(plugin_path):

        os.environ["QT_PLUGIN_PATH"] = plugin_path
