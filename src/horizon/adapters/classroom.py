import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
]


def autenticar():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


def verificar_acesso():
    try:
        creds = autenticar()
        service = build("classroom", "v1", credentials=creds)

        cursos = service.courses().list(courseStates=["ACTIVE"]).execute().get("courses", [])
        print(f"Turmas ativas encontradas: {len(cursos)}\n")

        for curso in cursos[:3]:  # limita às 3 primeiras turmas no teste inicial
            cid = curso["id"]
            nome = curso.get("name")
            print(f"=== Turma: {nome} (id={cid}) ===")

            avisos = service.courses().announcements().list(courseId=cid, pageSize=5).execute().get("announcements", [])
            print(f"  Postagens (amostra até 5): {len(avisos)}")
            for a in avisos:
                texto = (a.get("text") or "").replace("\n", " ").strip()
                print(f"    - Aviso: {texto[:70]}")

            atividades = service.courses().courseWork().list(courseId=cid, pageSize=5).execute().get("courseWork", [])
            print(f"  Atividades (amostra até 5): {len(atividades)}")
            for cw in atividades:
                sub = (
                    service.courses()
                    .courseWork()
                    .studentSubmissions()
                    .list(courseId=cid, courseWorkId=cw["id"], userId="me")
                    .execute()
                    .get("studentSubmissions", [])
                )
                nota = sub[0].get("assignedGrade") if sub else None
                status = sub[0].get("state") if sub else None
                print(f"    - {cw.get('title')} | prazo={cw.get('dueDate')} | status={status} | nota={nota}")

    except HttpError as err:
        print(f"Erro na API do Google Classroom (HTTP {err.resp.status}): {err}")


if __name__ == "__main__":
    verificar_acesso()