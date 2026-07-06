import json, re, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
HIST = DATA / "historico"
DATA.mkdir(exist_ok=True)
HIST.mkdir(parents=True, exist_ok=True)

SITES = [
    {"orgao":"CREMERS", "tipo":"Conselho", "url":"https://cremers.org.br/noticias/", "keywords":["resolução","portaria","ética","registro","direção técnica"]},
    {"orgao":"CFM", "tipo":"Conselho", "url":"https://portal.cfm.org.br/noticias/", "keywords":["resolução","parecer","norma","registro","ética"]},
    {"orgao":"COREN-RS", "tipo":"Conselho", "url":"https://www.portalcoren-rs.gov.br/index.php?categoria=publicacoes&pagina=noticias", "keywords":["resolução","inscrição","fiscalização","norma"]},
    {"orgao":"COFEN", "tipo":"Conselho", "url":"https://www.cofen.gov.br/category/noticias/", "keywords":["resolução","parecer","fiscalização","norma"]},
    {"orgao":"CRF-RS", "tipo":"Conselho", "url":"https://www.crfrs.org.br/noticias", "keywords":["resolução","farmácia","licença","fiscalização"]},
    {"orgao":"CRN-2", "tipo":"Conselho", "url":"https://www.crn2.org.br/noticias", "keywords":["resolução","nutrição","fiscalização","inscrição"]},
    {"orgao":"CRO-RS", "tipo":"Conselho", "url":"https://www.crors.org.br/noticias", "keywords":["resolução","odontologia","fiscalização","registro"]},
    {"orgao":"CRTR-6", "tipo":"Conselho", "url":"https://www.crtr6.gov.br/", "keywords":["resolução","radiologia","fiscalização","registro"]},
    {"orgao":"ANVISA", "tipo":"Agência", "url":"https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa", "keywords":["resolução","rdc","consulta pública","medicamento","produto para saúde","alerta"]},
    {"orgao":"Alertas ANVISA", "tipo":"Alerta", "url":"https://www.gov.br/anvisa/pt-br/assuntos/fiscalizacao-e-monitoramento/alertas", "keywords":["alerta","interdição","recolhimento","suspensão","cancelamento"]},
    {"orgao":"DOU", "tipo":"Diário Oficial", "url":"https://www.in.gov.br/consulta/-/buscar/dou?q=%28ANVISA%20OR%20ANS%20OR%20CFM%20OR%20COFEN%29&s=todos&exactDate=all&sortType=0", "keywords":["resolução","portaria","instrução normativa","despacho","anvisa","cfm","cofen"]},
]

HEADERS = {"User-Agent":"Mozilla/5.0 MonitoramentoRegulatorio/1.0"}
BR_TZ = timezone(timedelta(hours=-3))

def clean(txt):
    return re.sub(r"\s+", " ", txt or "").strip()

def prioridade(text, keywords):
    t = text.lower()
    criticas = ["suspensão", "interdição", "recolhimento", "cancelamento", "proibição", "alerta"]
    medias = ["resolução", "rdc", "portaria", "instrução normativa", "consulta pública"]
    if any(k in t for k in criticas): return "Ação imediata"
    if any(k in t for k in medias): return "Necessita avaliação"
    if any(k in t for k in [x.lower() for x in keywords]): return "Atenção"
    return "Informativo"

def coletar(site):
    fonte_status = {"orgao":site["orgao"], "url":site["url"], "status":"ok", "erro":""}
    itens=[]
    try:
        r = requests.get(site["url"], headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        candidatos=[]
        for a in soup.find_all("a", href=True):
            titulo = clean(a.get_text(" "))
            if len(titulo) < 18 or len(titulo) > 220: continue
            href = urljoin(site["url"], a["href"])
            if href.startswith("mailto:") or href.startswith("javascript:"): continue
            score = sum(1 for k in site["keywords"] if k.lower() in titulo.lower())
            candidatos.append((score, titulo, href))
        vistos=set()
        for score,titulo,href in sorted(candidatos, key=lambda x:(-x[0], x[1]))[:12]:
            chave = hashlib.sha1((site["orgao"]+titulo+href).encode("utf-8")).hexdigest()[:16]
            if chave in vistos: continue
            vistos.add(chave)
            itens.append({
                "id": chave,
                "orgao": site["orgao"],
                "tipo": site["tipo"],
                "titulo": titulo,
                "link": href,
                "data": datetime.now(BR_TZ).strftime("%d/%m/%Y"),
                "prioridade": prioridade(titulo, site["keywords"]),
                "resumo": "Item identificado automaticamente no monitoramento diário. Validar conteúdo e impacto regulatório.",
                "novo": True
            })
    except Exception as e:
        fonte_status["status"]="erro"
        fonte_status["erro"]=str(e)[:250]
    return fonte_status, itens

def main():
    fontes=[]; itens=[]
    for site in SITES:
        f, its = coletar(site)
        fontes.append(f); itens.extend(its)
    agora = datetime.now(BR_TZ)
    resultado = {
        "gerado_em": agora.strftime("%d/%m/%Y %H:%M"),
        "total": len(itens),
        "novos": len([i for i in itens if i.get("novo")]),
        "erros": len([f for f in fontes if f["status"] != "ok"]),
        "fontes": fontes,
        "itens": itens
    }
    (DATA/"resultado_atual.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (HIST/f"{agora.strftime('%Y-%m-%d')}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Monitoramento concluído: {len(itens)} itens, {resultado['erros']} erros")

if __name__ == "__main__":
    main()
