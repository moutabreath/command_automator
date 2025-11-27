from user.repository.mongo_user_persist import MongoUserPerist


class UserRegistryService:
    def __init__(self):
        self.logged_in_user = ""
        self.user_persist = MongoUserPerist()

    def login_or_register_user(self, user_email) -> str: 
        return self.user_persist.create_or_update_user(user_email)