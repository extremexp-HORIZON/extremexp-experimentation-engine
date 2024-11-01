import requests

def detect_fire(image_base64):
    """
    Sends a base64 encoded image to the fire detection API.
    :param image_base64: Base64 encoded image data
    :return: Boolean indicating whether fire is detected
    """
    response = requests.post("http://localhost:8081/detect_image", json={"image": image_base64})
    return response.json().get("detected", False)