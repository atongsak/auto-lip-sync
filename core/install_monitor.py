from ..core.dependency_manager import refresh_dependency_state

def monitor_install():
    global INSTALL_PROCESS, INSTALL_SCENE

    if INSTALL_PROCESS is None:
        return None

    setup = INSTALL_SCENE.setup

    line = INSTALL_PROCESS.stdout.readline()

    if line:
        setup.install_log = line.strip()

    if INSTALL_PROCESS.poll() is not None:
        # Consume any remaining output
        remaining = INSTALL_PROCESS.stdout.read()

        if remaining:
            lines = [l.strip() for l in remaining.splitlines() if l.strip()]
            if lines:
                setup.install_log = lines[-1]
                print(setup.install_log)

        if INSTALL_PROCESS.returncode == 0:
            setup.install_log = "Installation complete."
        else:
            setup.install_log = "Installation failed."

        setup.installing = False

        refresh_dependency_state(INSTALL_SCENE)

        INSTALL_PROCESS = None
        INSTALL_SCENE = None

        return None

    return 0.5