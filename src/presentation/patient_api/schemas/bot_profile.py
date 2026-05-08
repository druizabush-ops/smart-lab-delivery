from pydantic import BaseModel


class SaveBotLoginRequest(BaseModel):
    login: str


class SaveBotPasswordRequest(BaseModel):
    password: str


class BotSimpleResponse(BaseModel):
    ok: bool
    message: str


class BotMiniappTokenResponse(BaseModel):
    auto_login_token: str
