import pyawr.mwoffice as mwoffice
import time
import multiprocessing
import ctypes

class TreeLogger:
    """
    Custom logger for the awr_automation project.
    Formats terminal output in a tree-branch structure.
    """
    @staticmethod
    def log(message: str, level: int = 0, is_last: bool = False):
        if level == 0:
            print(f"\n[{message}]")
        else:
            prefix = "│   " * (level - 1)
            branch = "└── " if is_last else "├── "
            print(f"{prefix}{branch}{message}")


def process_monitor_popups(main_hwnd: int, timeout: float = 15.0):
    """
    Independent OS-level process to monitor and dismiss AWR pop-ups.
    Bypasses Python's GIL lock caused by synchronous COM execution.
    """
    # Windows API Constants for key injection
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    VK_RETURN = 0x0D # Enter key

    TreeLogger.log("Started independent multiprocessing popup monitor.", level=2)
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Retrieve the handle of the currently active/foreground window
        active_hwnd = ctypes.windll.user32.GetForegroundWindow()

        if active_hwnd != 0 and active_hwnd != main_hwnd:
            length = ctypes.windll.user32.GetWindowTextLengthW(active_hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(active_hwnd, buf, length + 1)
            window_title = buf.value

            # Verify if the foreground window title matches expected AWR pop-ups
            if any(keyword in window_title for keyword in ["Script", "Info", "AWR"]):
                time.sleep(0.2) # Give UI a fraction of a second to become responsive
                
                # Send 'Enter' directly to the window's message queue via Windows API
                ctypes.windll.user32.PostMessageW(active_hwnd, WM_KEYDOWN, VK_RETURN, 0)
                ctypes.windll.user32.PostMessageW(active_hwnd, WM_KEYUP, VK_RETURN, 0)
                
                TreeLogger.log(f"Popup bypassed via OS message queue: '{window_title}'", level=2, is_last=True)
                return

        time.sleep(0.1)

    TreeLogger.log("Process monitor finished. No interruptions detected.", level=2, is_last=True)


def run_load_pull_template_script():
    """
    Locates and executes the load pull template script within AWR Microwave Office.
    """
    TreeLogger.log("AWR Automation: Load Pull Template Execution")
    
    try:
        app = mwoffice.CMWOffice()
        main_hwnd = app.hWnd
        TreeLogger.log(f"Successfully connected to AWR instance (HWND: {main_hwnd}).", level=1)
    except Exception as e:
        TreeLogger.log(f"Failed to connect to AWR: {e}", level=1, is_last=True)
        return

    script_found = False

    for module in app.GlobalScripts:
        for routine in module.Routines:
            routine_name = routine.Name.lower()

            if "load" in routine_name and "pull" in routine_name and "template" in routine_name:
                script_found = True
                TreeLogger.log(f"Target routine located: {module.Name} -> {routine.Name}", level=1)

                # 1. Initialize an independent PROCESS (not a thread) to bypass GIL
                monitor_process = multiprocessing.Process(
                    target=process_monitor_popups, 
                    args=(main_hwnd, 15.0)
                )
                monitor_process.start()

                # 2. Execute the routine (Locks the main process GIL, but monitor runs free)
                TreeLogger.log("Executing AWR routine...", level=1)
                routine.Run()

                # 3. Wait for the monitor process to gracefully terminate
                monitor_process.join()
                
                TreeLogger.log("Routine execution sequence completed.", level=1, is_last=True)
                return

    if not script_found:
        TreeLogger.log("Target routine containing 'load', 'pull', 'template' was not found.", level=1, is_last=True)


if __name__ == "__main__":
    # Standard multiprocessing setup requirement for Windows
    multiprocessing.freeze_support() 
    run_load_pull_template_script()