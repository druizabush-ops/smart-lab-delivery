from fastapi import APIRouter, Header, HTTPException, Request

from src.presentation.patient_api.schemas.bot_profile import (
    BotMiniappTokenResponse,
    BotSimpleResponse,
    SaveBotLoginRequest,
    SaveBotPasswordRequest,
)

router = APIRouter(prefix="/bot", tags=["patient-bot"])


def _max_user_id(x_max_user_id: str | None) -> str:
    if not x_max_user_id:
        raise HTTPException(status_code=401, detail="Не удалось определить пользователя")
    return x_max_user_id


@router.post("/profile/save-login", response_model=BotSimpleResponse)
def save_login(payload: SaveBotLoginRequest, request: Request, x_max_user_id: str | None = Header(default=None)) -> BotSimpleResponse:
    use_case = request.app.state.bot_profile_use_case
    use_case.save_login(_max_user_id(x_max_user_id), payload.login)
    return BotSimpleResponse(ok=True, message="Логин сохранён.")


@router.post("/profile/save-password", response_model=BotSimpleResponse)
def save_password(payload: SaveBotPasswordRequest, request: Request, x_max_user_id: str | None = Header(default=None)) -> BotSimpleResponse:
    use_case = request.app.state.bot_profile_use_case
    use_case.save_password(_max_user_id(x_max_user_id), payload.password)
    return BotSimpleResponse(ok=True, message="Пароль сохранён.")


@router.post("/profile/check-login", response_model=BotSimpleResponse)
def check_login(request: Request, x_max_user_id: str | None = Header(default=None)) -> BotSimpleResponse:
    use_case = request.app.state.bot_check_login_use_case
    ok = use_case.execute(_max_user_id(x_max_user_id))
    if ok:
        return BotSimpleResponse(ok=True, message="Вход проверен. Теперь можно открывать приложение одной кнопкой.")
    return BotSimpleResponse(ok=False, message="Не удалось войти. Проверьте логин и пароль.")


@router.delete("/profile", response_model=BotSimpleResponse)
def delete_profile(request: Request, x_max_user_id: str | None = Header(default=None)) -> BotSimpleResponse:
    use_case = request.app.state.bot_profile_use_case
    use_case.delete_profile(_max_user_id(x_max_user_id))
    return BotSimpleResponse(ok=True, message="Профиль удалён.")


@router.post("/miniapp-token/create", response_model=BotMiniappTokenResponse)
def create_miniapp_token(request: Request, x_max_user_id: str | None = Header(default=None)) -> BotMiniappTokenResponse:
    profile_use_case = request.app.state.bot_profile_use_case
    user_id = _max_user_id(x_max_user_id)
    if not profile_use_case.has_credentials(user_id):
        raise HTTPException(status_code=400, detail="Профиль не заполнен")
    token = request.app.state.bot_miniapp_token_use_case.create(user_id)
    return BotMiniappTokenResponse(auto_login_token=token)
