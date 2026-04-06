from authentication.services import JWTService


def verify_jwt_and_get_user(request, User):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ", 1)[1]

    payload = JWTService.decode_token(token)

    if not payload:
        return None

    user = User.objects.filter(username=payload["username"]).first()
    if not user:
        return None

    return user
