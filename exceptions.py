class ScreenAlreadyExistsException(Exception):
    def __init__(self, screen_name: str):
        super().__init__(f"Screen {screen_name} already exist in the service.")
