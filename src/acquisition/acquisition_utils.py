import cv2



def get_video_fps(capture: cv2.VideoCapture) -> float:
    """Extrai a taxa de quadros nativa (FPS) de um objeto VideoCapture."""
    return capture.get(cv2.CAP_PROP_FPS)