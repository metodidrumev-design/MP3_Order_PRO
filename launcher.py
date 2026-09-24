# =====================================================
# MP3 ORDER PRO - LAUNCHER
# =====================================================

import os
import sys
import subprocess

from pathlib import Path

# =====================================================
# ПЪТ КЪМ ПРОГРАМАТА
# =====================================================

if getattr(
    sys,
    "frozen",
    False,
):

    BASE_DIR = Path(sys.executable).resolve().parent

else:

    BASE_DIR = Path(__file__).resolve().parent


# =====================================================
# ОСНОВНО EXE
# =====================================================

MAIN_EXE = BASE_DIR / "MP3_Order_PRO.exe"


# =====================================================
# СТАРТИРАМЕ ОСНОВНАТА ПРОГРАМА
# =====================================================

if MAIN_EXE.exists():

    try:

        launcher_environment = os.environ.copy()

        subprocess.Popen(
            [str(MAIN_EXE)],
            cwd=str(BASE_DIR),
            env=launcher_environment,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
        )

    except Exception:

        pass

else:

    # =================================================
    # АКО ОСНОВНИЯТ EXE ЛИПСВА
    # =================================================

    try:

        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0,
            (
                "MP3_Order_PRO.exe не е намерен."
                if os.environ.get("LANG", "").lower().startswith("en")
                else "MP3_Order_PRO.exe не е намерен."
            ),
            "MP3 Order PRO",
            0x10,
        )

    except Exception:

        pass


# =====================================================
# КРАЙ НА LAUNCHER
# =====================================================

sys.exit(0)
