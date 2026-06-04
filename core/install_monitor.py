from ..core.dependency_manager import refresh_dependency_state
from . import runtime_state 

def monitor_install():
    if runtime_state.INSTALL_PROCESS is None:
        print("No installation running. Stopping timer.")
        return None

    setup = runtime_state.INSTALL_SCENE.setup

    line = runtime_state.INSTALL_PROCESS.stdout.readline()

    if line:
        setup.install_log = line.strip()

    if runtime_state.INSTALL_PROCESS.poll() is not None:
        print("Installation complete")

        # Consume any remaining output
        remaining = runtime_state.INSTALL_PROCESS.stdout.read()

        if remaining:
            lines = [l.strip() for l in remaining.splitlines() if l.strip()]
            if lines:
                setup.install_log = lines[-1]
                print(setup.install_log)

        if runtime_state.INSTALL_PROCESS.returncode == 0:
            setup.install_log = "Installation complete."
        else:
            setup.install_log = "Installation failed."

        setup.installing = False

        refresh_dependency_state(runtime_state.INSTALL_SCENE)

        runtime_state.INSTALL_PROCESS = None
        runtime_state.INSTALL_SCENE = None

        return None

    return 0.5