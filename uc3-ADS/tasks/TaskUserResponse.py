class TaskUserResponse:
    def __init__(self):
        """
        Initialize the task for managing user responses.
        """
        pass

    def check_user_response(self, user_response):
        """
        Check if the user accepts or rejects the alert.
        :param user_response: User's response ("accept" or "reject")
        :return: Boolean indicating if the alert is accepted
        """
        return user_response == "accept"