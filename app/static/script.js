(function(){
  var sb=document.getElementById('sidebar'),bt=document.getElementById('menuBtn');
  if(bt)bt.onclick=function(){sb.classList.toggle('open')};
  document.addEventListener('click',function(e){if(sb&&sb.classList.contains('open')&&!sb.contains(e.target)&&e.target!==bt)sb.classList.remove('open')});
  // render Plotly charts passed from the server as {id: figureJSON}
  var C=window.CHARTS||{};
  Object.keys(C).forEach(function(id){var f=JSON.parse(C[id]),el=document.getElementById(id);
    if(el&&window.Plotly)Plotly.newPlot(el,f.data,f.layout,{responsive:true,displaylogo:false});});
  // auto-submit selects flagged with data-auto
  document.querySelectorAll('select[data-auto]').forEach(function(s){s.onchange=function(){s.form.submit()}});
})();
