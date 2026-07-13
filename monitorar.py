import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
HIST = DATA / "historico"
RESULTADO = DATA / "resultado_atual.json"
DATA.mkdir(exist_ok=True)
HIST.mkdir(parents=True, exist_ok=True)

SITES = [
    {"orgao":"CREMERS","tipo":"Conselho","url":"https://cremers.org.br/noticias/","keywords":["resolução","portaria","ética","registro","direção técnica"]},
    {"orgao":"CFM","tipo":"Conselho","url":"https://portal.cfm.org.br/noticias/","keywords":["resolução","parecer","norma","registro","ética"]},
    {"orgao":"COREN-RS","tipo":"Conselho","url":"https://www.portalcoren-rs.gov.br/index.php?categoria=publicacoes&pagina=noticias","keywords":["resolução","inscrição","fiscalização","norma"]},
    {"orgao":"COFEN","tipo":"Conselho","url":"https://www.cofen.gov.br/category/noticias/","keywords":["resolução","parecer","fiscalização","norma"]},
    {"orgao":"CRF-RS","tipo":"Conselho","url":"https://www.crfrs.org.br/noticias","keywords":["resolução","farmácia","licença","fiscalização"]},
    {"orgao":"CRN-2","tipo":"Conselho","url":"https://www.crn2.org.br/noticias","keywords":["resolução","nutrição","fiscalização","inscrição"]},
    {"orgao":"CRO-RS","tipo":"Conselho","url":"https://www.crors.org.br/noticias","keywords":["resolução","odontologia","fiscalização","registro"]},
    {"orgao":"CRTR-6","tipo":"Conselho","url":"https://www.crtr6.gov.br/","keywords":["resolução","radiologia","fiscalização","registro"]},
    {"orgao":"ANVISA","tipo":"Agência","url":"https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa","keywords":["resolução","rdc","consulta pública","medicamento","produto para saúde","alerta"]},
    {"orgao":"Alertas ANVISA","tipo":"Alerta","url":"https://www.gov.br/anvisa/pt-br/assuntos/fiscalizacao-e-monitoramento/alertas","keywords":["alerta","interdição","recolhimento","suspensão","cancelamento"]},
    {"orgao":"DOU","tipo":"Diário Oficial","url":"https://www.in.gov.br/consulta/-/buscar/dou?q=%28ANVISA%20OR%20CFM%20OR%20COFEN%20OR%20CREMERS%20OR%20COREN%29&s=todos&exactDate=all&sortType=0","keywords":["resolução","portaria","instrução normativa","despacho","anvisa","cfm","cofen"]}
]
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"pt-BR,pt;q=0.9"}
BR_TZ=timezone(timedelta(hours=-3))

def clean(txt): return re.sub(r"\s+"," ",txt or "").strip()

def prioridade(text, keywords):
    t=text.lower()
    if any(k in t for k in ["suspensão","interdição","recolhimento","cancelamento","proibição","alerta"]): return "Ação imediata"
    if any(k in t for k in ["resolução","rdc","portaria","instrução normativa","consulta pública","edital"]): return "Necessita avaliação"
    if any(k.lower() in t for k in keywords): return "Atenção"
    return "Informativo"

def anteriores():
    if not RESULTADO.exists(): return set()
    try:
        obj=json.loads(RESULTADO.read_text(encoding="utf-8"))
        return {str(i.get("id")) for i in obj.get("itens",[]) if i.get("id")}
    except Exception:
        return set()

def link_valido(url, origem):
    try:
        p=urlparse(url)
        return p.scheme in {"http","https"} and not url.lower().endswith((".jpg",".jpeg",".png",".gif",".svg",".css",".js"))
    except Exception:
        return False

def coletar(site, ids_antigos):
    status={"orgao":site["orgao"],"url":site["url"],"status":"ok","erro":"","quantidade":0}
    itens=[]
    try:
        r=requests.get(site["url"],headers=HEADERS,timeout=35,allow_redirects=True)
        r.raise_for_status()
        soup=BeautifulSoup(r.text,"lxml")
        candidatos=[]
        for a in soup.find_all("a",href=True):
            titulo=clean(a.get_text(" "))
            if not 18 <= len(titulo) <= 240: continue
            href=urljoin(r.url,a["href"])
            if not link_valido(href,r.url): continue
            if titulo.lower() in {"notícias","início","saiba mais","leia mais","ver todas"}: continue
            score=sum(1 for k in site["keywords"] if k.lower() in titulo.lower())
            candidatos.append((score,titulo,href))
        vistos=set()
        for score,titulo,href in sorted(candidatos,key=lambda x:(-x[0],x[1])):
            chave=hashlib.sha1(f"{site['orgao']}|{titulo}|{href}".encode("utf-8")).hexdigest()[:16]
            if chave in vistos: continue
            vistos.add(chave)
            itens.append({"id":chave,"orgao":site["orgao"],"tipo":site["tipo"],"titulo":titulo,"link":href,
                          "data":datetime.now(BR_TZ).strftime("%d/%m/%Y"),"prioridade":prioridade(titulo,site["keywords"]),
                          "resumo":"Publicação identificada automaticamente. Validar conteúdo e impacto regulatório.",
                          "novo":chave not in ids_antigos,"relevancia":score})
            if len(itens)>=12: break
        status["quantidade"]=len(itens)
    except Exception as e:
        status["status"]="erro";status["erro"]=clean(str(e))[:300]
    return status,itens

def main():
    ids_antigos=anteriores()
    fontes=[];itens=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        tarefas=[ex.submit(coletar,s,ids_antigos) for s in SITES]
        for t in as_completed(tarefas):
            f,its=t.result();fontes.append(f);itens.extend(its)
    ordem={"Ação imediata":0,"Necessita avaliação":1,"Atenção":2,"Informativo":3}
    itens.sort(key=lambda i:(ordem.get(i["prioridade"],9),-int(i.get("relevancia",0)),i["orgao"],i["titulo"]))
    fontes.sort(key=lambda f:f["orgao"])
    agora=datetime.now(BR_TZ)
    resultado={"gerado_em":agora.strftime("%d/%m/%Y %H:%M"),"total":len(itens),
               "novos":sum(1 for i in itens if i.get("novo")),
               "erros":sum(1 for f in fontes if f["status"]!="ok"),"fontes":fontes,"itens":itens}
    conteudo=json.dumps(resultado,ensure_ascii=False,indent=2)
    RESULTADO.write_text(conteudo,encoding="utf-8")
    (HIST/f"{agora.strftime('%Y-%m-%d_%H-%M')}.json").write_text(conteudo,encoding="utf-8")
    print(f"Monitoramento concluído: {len(itens)} itens, {resultado['novos']} novos, {resultado['erros']} erros.")

if __name__=="__main__":
    main()
