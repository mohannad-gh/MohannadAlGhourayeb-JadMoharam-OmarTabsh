# Print test login tokens for each role - FOR LOCAL DEVELOPMENT ONLY
# Omar Tabsh - 202400798
#
# Until the Users service (POST /users/login) is merged, this creates tokens signed
# with the shared JWT_SECRET_KEY from .env so the services can be tested in Postman.
# For the final report evidence, use tokens returned by the real POST /users/login.
#
#   python -m scripts.dev_token                 -> one token per role
#   python -m scripts.dev_token analyst 12      -> token for role "analyst", user_id 12

import sys

from common.auth import create_token
from common.roles import ALL_ROLES

DEFAULT_USER_IDS = {"admin": 1, "analyst": 2, "user": 3, "auditor": 4}


def main(args):
    if args:
        role = args[0]
        user_id = int(args[1]) if len(args) > 1 else DEFAULT_USER_IDS.get(role, 1)
        print(create_token(user_id, f"{role}_dev", role, expires_minutes=24 * 60))
        return
    for role in ALL_ROLES:
        token = create_token(DEFAULT_USER_IDS[role], f"{role}_dev", role, expires_minutes=24 * 60)
        print(f"{role} (user_id {DEFAULT_USER_IDS[role]}):\n{token}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
