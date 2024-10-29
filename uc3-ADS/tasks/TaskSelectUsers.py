import requests

class TaskSelectUsers:
    def __init__(self, user_service_url, osrm_url):
        """
        Initialize the user selection task with URLs for user service and OSRM.
        :param user_service_url: API URL for user data
        :param osrm_url: OSRM API URL for distance calculation
        """
        self.user_service_url = user_service_url
        self.osrm_url = osrm_url

    def get_all_users(self):
        """
        Retrieve the list of all users from the API.
        :return: List of users with their details
        """
        response = requests.get(f"{self.user_service_url}/readall")
        return response.json() if response.status_code == 200 else []

    def calculate_distance(self, loc1, loc2):
        """
        Calculate the driving distance between two coordinates using OSRM.
        :param loc1: Coordinates of the alert (latitude, longitude)
        :param loc2: Coordinates of a user (latitude, longitude)
        :return: Distance in kilometers
        """
        response = requests.get(f"{self.osrm_url}/route/v1/driving/{loc1[1]},{loc1[0]};{loc2[1]},{loc2[0]}?overview=false")
        return response.json()['routes'][0]['distance'] / 1000 if response.status_code == 200 else float('inf')

    def select_nearest_users(self, alert_location, num_users=2):
        """
        Select the closest available users to the alert location.
        :param alert_location: GPS coordinates of the alert
        :param num_users: Number of users to select
        :return: List of selected users
        """
        users = self.get_all_users()
        users_with_distance = [(user, self.calculate_distance(alert_location, (user['latitude'], user['longitude'])))
                               for user in users if 'latitude' in user and 'longitude' in user]

        return sorted(users_with_distance, key=lambda x: x[1])[:num_users]