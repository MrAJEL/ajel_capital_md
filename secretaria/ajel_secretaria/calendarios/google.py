"""Google Calendar provider (Calendar API v3).

Requires the optional dependencies: ``pip install -e ".[google]"``.
"""

from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from ..modelos import Evento

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def conectar_google(credenciales: Path, token: Path):
    """Return an authorized Calendar API service.

    The first run opens the browser for Google's consent screen and stores ``token``.
    ``credenciales`` is the OAuth client file ("Desktop app") downloaded from Google Cloud.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token.is_file():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credenciales.is_file():
                raise FileNotFoundError(
                    f"No encuentro {credenciales}. Descárgalo de Google Cloud Console "
                    "(OAuth client, tipo 'Desktop app'). Ver secretaria/README.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credenciales), SCOPES)
            creds = flow.run_local_server(port=0)
        token.parent.mkdir(parents=True, exist_ok=True)
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


class CalendarioGoogle:
    def __init__(
        self,
        servicio,
        calendario_id: str = "primary",
        zona_horaria: str = "America/Mexico_City",
        enviar_invitaciones: str = "all",  # all | externalOnly | none
    ) -> None:
        self._eventos = servicio.events()
        self._calendario = calendario_id
        self._zona = zona_horaria
        self._tz = ZoneInfo(zona_horaria)
        self._enviar = enviar_invitaciones

    def listar_eventos(self, desde: datetime, hasta: datetime) -> list[Evento]:
        eventos: list[Evento] = []
        pagina = None
        while True:
            respuesta = self._eventos.list(
                calendarId=self._calendario,
                timeMin=desde.isoformat(),
                timeMax=hasta.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
                pageToken=pagina,
            ).execute()
            eventos += [
                self._a_evento(item)
                for item in respuesta.get("items", [])
                if item.get("status") != "cancelled"
            ]
            pagina = respuesta.get("nextPageToken")
            if not pagina:
                return eventos

    def obtener_evento(self, evento_id: str) -> Evento | None:
        from googleapiclient.errors import HttpError

        try:
            item = self._eventos.get(calendarId=self._calendario, eventId=evento_id).execute()
        except HttpError as error:
            if error.resp.status in (404, 410):
                return None
            raise
        return None if item.get("status") == "cancelled" else self._a_evento(item)

    def crear_evento(self, titulo, inicio, fin, invitados, descripcion, ubicacion) -> Evento:
        cuerpo = {
            "summary": titulo,
            "description": descripcion,
            "location": ubicacion,
            "start": self._momento(inicio),
            "end": self._momento(fin),
            "attendees": [{"email": correo} for correo in invitados],
        }
        item = self._eventos.insert(
            calendarId=self._calendario, body=cuerpo, sendUpdates=self._enviar
        ).execute()
        return self._a_evento(item)

    def mover_evento(self, evento_id: str, inicio: datetime, fin: datetime) -> Evento:
        item = self._eventos.patch(
            calendarId=self._calendario,
            eventId=evento_id,
            body={"start": self._momento(inicio), "end": self._momento(fin)},
            sendUpdates=self._enviar,
        ).execute()
        return self._a_evento(item)

    def cancelar_evento(self, evento_id: str) -> None:
        self._eventos.delete(
            calendarId=self._calendario, eventId=evento_id, sendUpdates=self._enviar
        ).execute()

    def _momento(self, momento: datetime) -> dict[str, str]:
        return {"dateTime": momento.isoformat(), "timeZone": self._zona}

    def _leer_momento(self, dato: dict) -> datetime:
        if "dateTime" in dato:
            return datetime.fromisoformat(dato["dateTime"]).astimezone(self._tz)
        # All-day event: "date" is YYYY-MM-DD, the end date is exclusive.
        return datetime.combine(date.fromisoformat(dato["date"]), time(0), self._tz)

    def _a_evento(self, item: dict) -> Evento:
        return Evento(
            id=item["id"],
            titulo=item.get("summary", "(sin título)"),
            inicio=self._leer_momento(item["start"]),
            fin=self._leer_momento(item["end"]),
            invitados=tuple(a["email"] for a in item.get("attendees", []) if "email" in a),
            descripcion=item.get("description", ""),
            ubicacion=item.get("location", ""),
            ocupa=item.get("transparency", "opaque") != "transparent",
        )
