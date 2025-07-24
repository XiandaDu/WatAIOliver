from fastapi import HTTPException, Request, status


def get_current_user(request: Request):
    user = request.session.get("session_user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    return user
