# -*- coding: utf-8 -*-
"""
Monitoramento Regulatório Diário — Unimed Vale do Sinos/RS
Versão 4.1 — ANS fora do escopo; motor em nuvem, histórico diário e backup completo.
"""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
HIST = DATA / "historico"
RESULTADO = DATA / "resultado_atual.json"
RESULTADO_RAIZ = BASE / "resultado_atual.json"  # compatibilidade com versões anteriores
DATA.mkdir(parents=True, exist_ok=True)
HIST.mkdir(parents=True, exist_ok=True)

TZ_BR = timezone(timedelta(hours=-3))
AGORA = datetime.now(TZ_BR)
HOJE = AGORA.date().isoformat()
ANO = str(AGORA.year)

FONTES = [
    {"fonte":"CREMERS","tipo":"NOTÍCIA","url":"https://cremers.org.br/noticias/","termos":["resolução","portaria","ética","registro","direção técnica"]},
    {"fonte":"CFM","tipo":"NOTÍCIA","url":"https://portal.cfm.org.br/noticias/","termos":["resolução","parecer","norma","registro","ética"]},
    {"fonte":"COREN-RS","tipo":"NOTÍCIA","url":"https://www.portalcoren-rs.gov.br/index.php?categoria=publicacoes&pagina=noticias","termos":["resolução","inscrição","fiscalização","norma"]},
    {"fonte":"COFEN","tipo":"NOTÍCIA","url":"https://www.cofen.gov.br/category/noticias/","termos":["resolução","parecer","fiscalização","norma"]},
    {"fonte":"CRF-RS","tipo":"NOTÍCIA","url":"https://www.crfrs.org.br/noticias","termos":["resolução","farmácia","licença","fiscalização"]},
    {"fonte":"CRN-2","tipo":"NOTÍCIA","url":"https://www.crn2.org.br/noticias","termos":["resolução","nutrição","fiscalização","inscrição"]},
    {"fonte":"CRO-RS","tipo":"NOTÍCIA","url":"https://www.crors.org.br/noticias","termos":["resolução","odontologia","fiscalização","registro"]},
    {"fonte":"CRTR-6","tipo":"NOTÍCIA","url":"https://www.crtr6.gov.br/","termos":["resolução","radiologia","fiscalização","registro"]},
    {"fonte":"ANVISA","tipo":"NOTÍCIA","url":"https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa","termos":["resolução","rdc","consulta pública","medicamento","produto para saúde","alerta"]},
    {"fonte":"ALERTAS ANVISA","tipo":"ALERTA ANVISA","url":"https://www.gov.br/anvisa/pt-br/assuntos/fiscalizacao-e-monitoramento/alertas","termos":["alerta","interdição","recolhimento","suspensão","cancelamento"]},
    {"fonte":"DOU","tipo":"DOU","url":"https://www.in.gov.br/consulta/-/buscar/dou?q=%28ANVISA%20OR%20CFM%20OR%20COFEN%20OR%20CREMERS%20OR%20COREN%29&s=todos&exactDate=all&sortType=0","termos":["resolução","portaria","instrução normativa","despacho","anvisa","cfm","cofen"]}
]

HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language":"pt-BR,pt;q=0.9,en;q=0.7"
}

# Regras da IT-SUP-9.0244 aplicáveis ao projeto.
DESCARTAR = [
    "cosmético","cosmetico","fumo","tabaco","assunto trabalhista","ensaios clínicos","ensaio clínico",
    "uso in vitro","deferimento","indeferimento","certificação de boas práticas",
    "autorização de funcionamento de empresa"," afe ",
    "equipamento médico","equipamentos médicos","sistemas e equipamentos"
]

# A parte da ANS foi expressamente retirada do escopo deste projeto.
EXCLUIR_ANS = [
    "agência nacional de saúde suplementar",
    "agencia nacional de saude suplementar",
    "ans",
    "saúde suplementar",
    "saude suplementar",
    "tiss",
    "idss",
    "nip",
    "ressarcimento ao sus",
    "rol de procedimentos"
]

MONITORAR = [
    "medicamento","farmácia","farmacia","bula","produto para saúde","saneante","alimento","fórmula infantil",
    "vigilância sanitária","rdc","resolução","instrução normativa","portaria","lei","decreto","consulta pública",
    "alerta","recolhimento","suspensão","cancelamento de registro","hemoterapia","transplante","banco de sangue",
    "prescrição eletrônica","receituário","sncr","enfermagem","nutrição","odontologia","radiologia"
]

IGNORAR = {
    "notícias","noticias","início","inicio","portal","serviços","servicos","menu","acessibilidade",
    "mapa do site","contato","ouvidoria","transparência","transparencia","saiba mais","leia mais","ver todas"
}

def norm(texto):
    return re.sub(r"\s+"," ",texto or "").strip()

def identificador(fonte, titulo, link):
    return hashlib.sha1(f"{fonte}|{titulo}|{link}".encode("utf-8")).hexdigest()[:18]

def carregar_ids_anteriores():
    if not RESULTADO.exists():
        return set()
    try:
        anterior=json.loads(RESULTADO.read_text(encoding="utf-8"))
        return {str(x.get("id")) for x in anterior.get("publicacoes",[]) if x.get("id")}
    except Exception:
        return set()

def fora_escopo_ans(texto):
    """Retorna True quando o conteúdo pertence à rotina da ANS, excluída deste projeto."""
    t = " " + norm(texto).lower() + " "
    return any(termo in t for termo in EXCLUIR_ANS)

def decisao(texto):
    t=" "+norm(texto).lower()+" "
    for termo in DESCARTAR:
        if termo in t:
            return "Descartar","Baixo",f"Regra de descarte aplicada: {termo}."
    for termo in MONITORAR:
        if termo in t:
            return "Registrar/Encaminhar","Médio",f"Termo de interesse identificado: {termo}."
    return "Descartar","Baixo","Sem termo de interesse identificado nas regras atuais."

def macrotema(texto):
    t=norm(texto).lower()
    if any(x in t for x in ["medicamento","farmácia","farmacia","bula","receituário","sncr"]): return "Medicamentos"
    if any(x in t for x in ["saneante","produto irregular","recolhimento"]): return "Saneantes / Produtos irregulares"
    if any(x in t for x in ["enfermagem","cofen","coren"]): return "Enfermagem / Protocolos assistenciais"
    if any(x in t for x in ["nutrição","alimento","fórmula infantil"]): return "Nutrição / Alimentos"
    if any(x in t for x in ["odontologia","cro"]): return "Odontologia"
    if any(x in t for x in ["radiologia","crtr"]): return "Radiologia"
    return "Revisão manual"

def areas(texto):
    t=norm(texto).lower()
    lista=["Regulamentação e Parametrização"]
    regras=[
        ("Farmácia",["medicamento","farmácia","bula","receituário","sncr"]),
        ("Compras",["produto irregular","recolhimento","suspensão","cancelamento"]),
        ("Tecnologia da Informação",["sistema","integração","api","eletrônica"]),
        ("Enfermagem",["enfermagem","cofen","coren"]),
        ("Nutrição",["nutrição","alimento","fórmula infantil"]),
        ("Odontologia",["odontologia","cro"]),
        ("Radiologia",["radiologia","crtr"]),
        ("Corpo Clínico",["prescrição","receituário","cfm","cremers"])
    ]
    for area, termos in regras:
        if any(x in t for x in termos):
            lista.insert(0,area)
    return "; ".join(dict.fromkeys(lista))

def link_valido(link):
    try:
        p=urlparse(link)
        return p.scheme in {"http","https"} and not link.lower().endswith((".jpg",".jpeg",".png",".gif",".svg",".css",".js",".ico"))
    except Exception:
        return False

def consultar(site, ids_anteriores):
    resposta=requests.get(site["url"],headers=HEADERS,timeout=40,allow_redirects=True)
    resposta.raise_for_status()
    soup=BeautifulSoup(resposta.text,"html.parser")
    candidatos=[]
    for a in soup.find_all("a",href=True):
        titulo=norm(a.get_text(" "))
        if not 18 <= len(titulo) <= 260 or titulo.lower() in IGNORAR:
            continue
        link=urljoin(resposta.url,a.get("href",""))
        if not link_valido(link):
            continue
        score=sum(1 for termo in site["termos"] if termo.lower() in titulo.lower())
        candidatos.append((score,titulo,link))

    vistos=set()
    itens=[]
    for score,titulo,link in sorted(candidatos,key=lambda x:(-x[0],x[1])):
        chave=identificador(site["fonte"],titulo,link)
        if chave in vistos:
            continue
        vistos.add(chave)
        texto=f"{titulo} {link}"
        if fora_escopo_ans(texto):
            continue
        dec,impacto,just=decisao(texto)
        tipo=site["tipo"]
        data_dou=HOJE if tipo=="DOU" else "N/A"
        data_pub="N/A" if tipo=="DOU" else HOJE
        itens.append({
            "id":chave,
            "selected":True,
            "approved":False,
            "fonte":site["fonte"],
            "tipo":tipo,
            "titulo":titulo,
            "numero":"S/N",
            "ano":ANO,
            "dataDOU":data_dou,
            "dataPub":data_pub,
            "data_publicacao":HOJE,
            "assunto":titulo,
            "resumo":titulo,
            "macrotema":macrotema(texto),
            "status":"Vigente",
            "altRev":"N/A",
            "vigencia":HOJE,
            "areas":areas(texto),
            "aplicacao":"-",
            "acoes":"Comunicar áreas envolvidas e avaliar necessidade de ação interna, quando aplicável." if dec=="Registrar/Encaminhar" else "-",
            "link":link,
            "decisao":dec,
            "impacto":impacto,
            "justificativa":just,
            "regra":"MOTOR-V4.1-IT-SEM-ANS",
            "novo":chave not in ids_anteriores,
            "relevancia":score
        })
        if len(itens)>=20:
            break
    return itens

def main():
    ids_anteriores=carregar_ids_anteriores()
    publicacoes=[]
    fontes_status=[]
    erros=[]

    with ThreadPoolExecutor(max_workers=6) as executor:
        tarefas={executor.submit(consultar,site,ids_anteriores):site for site in FONTES}
        for tarefa in as_completed(tarefas):
            site=tarefas[tarefa]
            try:
                itens=tarefa.result()
                publicacoes.extend(itens)
                fontes_status.append({"fonte":site["fonte"],"status":"ok","quantidade":len(itens),"url":site["url"]})
            except Exception as exc:
                erro=norm(str(exc))[:350]
                fontes_status.append({"fonte":site["fonte"],"status":"erro","quantidade":0,"url":site["url"],"erro":erro})
                erros.append({"fonte":site["fonte"],"erro":erro})

    ordem={"Registrar/Encaminhar":0,"Descartar":1}
    publicacoes.sort(key=lambda x:(ordem.get(x["decisao"],9),-int(x.get("relevancia",0)),x["fonte"],x["titulo"]))
    fontes_status.sort(key=lambda x:x["fonte"])

    saida={
        "versao":"4.1-sem-ans-backup-completo",
        "gerado_em":AGORA.isoformat(),
        "fontes_monitoradas":[x["fonte"] for x in FONTES],
        "fontes_status":fontes_status,
        "total_publicacoes":len(publicacoes),
        "total_registrar_encaminhar":sum(1 for p in publicacoes if p["decisao"]=="Registrar/Encaminhar"),
        "total_descartar":sum(1 for p in publicacoes if p["decisao"]=="Descartar"),
        "total_novos":sum(1 for p in publicacoes if p.get("novo")),
        "erros":erros,
        "publicacoes":publicacoes
    }

    conteudo=json.dumps(saida,ensure_ascii=False,indent=2)
    RESULTADO.write_text(conteudo,encoding="utf-8")
    RESULTADO_RAIZ.write_text(conteudo,encoding="utf-8")
    (HIST/f"resultado_{AGORA.strftime('%Y-%m-%d_%H-%M')}.json").write_text(conteudo,encoding="utf-8")
    print(f"Monitoramento concluído: {len(publicacoes)} publicações; {len(erros)} erros.")

if __name__=="__main__":
    main()
