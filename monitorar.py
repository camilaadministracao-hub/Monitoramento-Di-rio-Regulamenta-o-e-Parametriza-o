import json, re, hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'config'/'fontes.json'
OUT=ROOT/'data'/'resultado_atual.json'
HIST=ROOT/'data'/'historico'
HEADERS={'User-Agent':'Mozilla/5.0 Monitoramento-Regulatorio/3.0'}

def prioridade(texto,palavras):
    t=texto.lower()
    pontos=sum(1 for p in palavras if p.lower() in t)
    if any(x in t for x in ['suspensão','interdição','recolhimento','ação imediata']): return 'Crítica'
    if pontos>=3: return 'Alta'
    if pontos>=1: return 'Média'
    return 'Baixa'

def resumo(t):
    t=re.sub(r'\s+',' ',t).strip()
    return t[:220]+('...' if len(t)>220 else '')

def coletar(fonte,palavras):
    r=requests.get(fonte['url'],headers=HEADERS,timeout=25)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    itens=[]; vistos=set()
    for a in soup.select(fonte.get('seletor') or 'a'):
        titulo=a.get_text(' ',strip=True)
        href=a.get('href')
        if not titulo or len(titulo)<18 or not href: continue
        url=urljoin(fonte['url'],href)
        chave=hashlib.sha1((fonte['orgao']+titulo+url).encode('utf-8')).hexdigest()
        if chave in vistos: continue
        vistos.add(chave)
        pr=prioridade(titulo,palavras)
        itens.append({'id':chave,'orgao':fonte['orgao'],'tipo':fonte.get('tipo','Notícias'),'titulo':titulo,'data':datetime.now().strftime('%d/%m/%Y'),'prioridade':pr,'resumo':resumo(titulo),'url':url})
        if len(itens)>=12: break
    return itens

def main():
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    itens=[]; erros=[]; consultas=0
    for fonte in cfg['fontes']:
        if not fonte.get('ativo',True): continue
        consultas+=1
        try: itens.extend(coletar(fonte,cfg.get('palavras_alerta',[])))
        except Exception as e: erros.append({'orgao':fonte.get('orgao','Fonte'),'erro':str(e)[:180]})
    alertas=sum(1 for i in itens if i['prioridade'] in ['Alta','Crítica'])
    agora=datetime.now().strftime('%d/%m/%Y %H:%M')
    dados={'gerado_em':agora,'total_consultas':consultas,'total_itens':len(itens),'novidades':len(itens),'alertas':alertas,'erros':erros,'itens':itens}
    OUT.parent.mkdir(parents=True,exist_ok=True); HIST.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf-8')
    (HIST/(datetime.now().strftime('%Y-%m-%d')+'.json')).write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
