from TaskFireDetection import detect_fire
from TaskSelectUsers import TaskSelectUsers
from TaskUserResponse import TaskUserResponse
import requests

class MainWorkflow:
    def __init__(self, image_base64, alert_location, user_service_url, osrm_url, user_response):
        """
        Initialize the main workflow with necessary parameters.
        :param image_base64: Base64 encoded image for fire detection
        :param alert_location: Coordinates (latitude, longitude) of the alert
        :param user_service_url: API URL to fetch user data
        :param osrm_url: URL of the OSRM service for calculating distances
        :param user_response: User's response to the alert (accept or reject)
        """
        self.image_base64 = image_base64
        self.alert_location = alert_location
        self.user_service_url = user_service_url
        self.osrm_url = osrm_url
        self.user_response = user_response

    def run_workflow(self):
        """
        Run the entire workflow by executing each task in sequence.
        :return: Final workflow results including fire detection, selected users, and alert acceptance status
        """
        # Task 1: Fire Detection
        print("Starting Task 1: Fire Detection")
        fire_detected = detect_fire(self.image_base64)
        if not fire_detected:
            print("No fire detected. Workflow ending.")
            return {"fire_detected": False, "selected_users": [], "alert_accepted": False}
        
        print("Fire detected. Proceeding to Task 2: Select Users")

        # Task 2: Select Users
        user_selector = TaskSelectUsers(self.user_service_url, self.osrm_url)
        selected_users = user_selector.select_nearest_users(self.alert_location)
        if not selected_users:
            print("No available users nearby. Workflow ending.")
            return {"fire_detected": True, "selected_users": [], "alert_accepted": False}
        
        print(f"Selected users: {[user[0]['uuid'] for user in selected_users]}")

        # Task 3: User Response
        response_manager = TaskUserResponse()
        alert_accepted = response_manager.check_user_response(self.user_response)
        
        if alert_accepted:
            print("User has accepted the alert.")
        else:
            print("User has rejected the alert.")
        
        # Final results
        return {
            "fire_detected": True,
            "selected_users": [user[0] for user in selected_users],
            "alert_accepted": alert_accepted
        }


if __name__ == "__main__":
    # Example data for testing
    image_base64 = "base64EncodedImageString"  # Replace with actual base64 image
    alert_location = (48.79842194845064, 1.9707823090763419)  # Replace with actual coordinates
    user_service_url = "http://localhost:16040/users"
    osrm_url = "http://localhost:5000"
    user_response = "accept"  # Example response; can be "accept" or "reject"
    
    # Initialize and run the main workflow
    workflow = MainWorkflow(image_base64, alert_location, user_service_url, osrm_url, user_response)
    results = workflow.run_workflow()
    print("Workflow results:", results)