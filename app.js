const REPO_ACTIONS_URL='https://github.com/camilaadministracao-hub/Monitoramento-Di-rio-Regulamenta-o-e-Parametriza-o/actions/workflows/monitoramento.yml';
let dados={itens:[],fontes:[]};
const $=id=>document.getElementById(id);
function cls(p){return p==='Ação imediata'?'danger':p==='Necessita avaliação'?'warn':'info'}
async function carregar(){
  try{
    const r=await fetch('data/resultado_atual.json?ts='+Date.now());
    if(!r.ok) throw new Error('HTTP '+r.status);
    dados=await r.json();
    render();
  }catch(e){
    $('lista').innerHTML='<article>Não foi possível carregar <strong>data/resultado_atual.json</strong>. Rode o Actions primeiro.</article>';
    $('resumo').textContent='Aguardando a primeira execução do robô.';
  }
}
function render(){
  const now=new Date();
  $('agora').textContent='Tela atualizada em '+now.toLocaleString('pt-BR');
  $('atualizacao').textContent=dados.gerado_em||'--';
  $('total').textContent=dados.total||0;
  $('erros').textContent=dados.erros||0;
  $('alertas').textContent=(dados.itens||[]).filter(i=>['Ação imediata','Necessita avaliação'].includes(i.prioridade)).length;
  $('resumo').textContent=`Monitoramento carregado com ${dados.total||0} publicação(ões), ${dados.novos||0} nova(s) e ${dados.erros||0} fonte(s) com erro.`;
  const orgs=[...new Set([...(dados.itens||[]).map(i=>i.orgao),...(dados.fontes||[]).map(f=>f.orgao)])].sort();
  $('orgao').innerHTML='<option value="">Todos os órgãos</option>'+orgs.map(o=>`<option>${o}</option>`).join('');
  renderLista();renderFontes();
}
function renderLista(){
  const q=$('busca').value.toLowerCase();
  const org=$('orgao').value;
  const itens=(dados.itens||[]).filter(i=>(!org||i.orgao===org)&&[i.orgao,i.titulo,i.prioridade,i.tipo,i.resumo].join(' ').toLowerCase().includes(q));
  $('lista').innerHTML=itens.length?itens.map(i=>`<article><div class="meta"><span class="tag">${i.orgao}</span><span class="tag">${i.tipo}</span><span class="tag ${cls(i.prioridade)}">${i.prioridade}</span><span class="tag">${i.data||'sem data'}</span>${i.novo?'<span class="tag">NOVO</span>':''}</div><h3>${i.titulo}</h3><p>${i.resumo||''}</p><a href="${i.link}" target="_blank" rel="noopener">Abrir publicação</a></article>`).join(''):'<article>Nenhum item encontrado para o filtro.</article>';
}
function renderFontes(){
  $('fontesLista').innerHTML=(dados.fontes||[]).map(f=>`<div><b>${f.orgao}</b><p class="${f.status==='ok'?'ok':'erro'}">${f.status==='ok'?'Online/consultado':'Erro na consulta'}</p><small>${f.status==='ok'?(f.quantidade||0)+' item(ns) encontrado(s)':f.erro}</small></div>`).join('') || '<div>Aguardando primeira execução.</div>';
}
function exportar(){
  const rows=[['Órgão','Tipo','Prioridade','Novo','Data','Título','Resumo','Link'],...(dados.itens||[]).map(i=>[i.orgao,i.tipo,i.prioridade,i.novo?'Sim':'Não',i.data,i.titulo,i.resumo,i.link])];
  const csv=rows.map(r=>r.map(c=>'"'+String(c||'').replaceAll('"','""')+'"').join(';')).join('\n');
  const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='monitoramento_regulatorio_unimed.csv';a.click();URL.revokeObjectURL(a.href);
}
$('busca').addEventListener('input',renderLista);
$('orgao').addEventListener('change',renderLista);
$('exportBtn').addEventListener('click',exportar);
$('runBtn').addEventListener('click',()=>window.open(REPO_ACTIONS_URL,'_blank'));
carregar();
