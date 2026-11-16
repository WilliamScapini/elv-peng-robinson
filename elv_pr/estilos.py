"""Estilo do relatório HTML local."""
CSS = """
:root {
  color-scheme: light dark;
  --fundo:#ffffff; --papel:#f5f6fb; --texto:#172033; --suave:#5f687d;
  --borda:#dce1eb; --acento:#3157c8; --secundaria:#df861b;
  --terciaria:#008b83; --alerta:#a85a08; --erro:#bd3434;
  --grade:#e8ecf3; --sucesso:#187a47; --lum:44%;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fundo:#101525; --papel:#1a2236; --texto:#edf1fa; --suave:#aab4ca;
    --borda:#303b55; --acento:#91a9ff; --secundaria:#ffbd66;
    --terciaria:#58d1c7; --alerta:#e9ab58; --erro:#ff8585;
    --grade:#2a354d; --sucesso:#66cf95; --lum:66%;
  }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--fundo); color:var(--texto);
       font:15px/1.62 system-ui,-apple-system,"Segoe UI",Arial,sans-serif; }
main { max-width:1120px; margin:0 auto; padding:38px 25px 76px; }
h1 { margin:0 0 8px; font-size:2.15rem; line-height:1.18; letter-spacing:-.035em; }
h2 { margin:48px 0 15px; padding-top:14px; border-top:2px solid var(--texto);
     font-size:1.35rem; letter-spacing:-.02em; }
h3 { margin:20px 0 8px; font-size:1rem; }
p { margin:8px 0 13px; }
.sub { color:var(--suave); margin:0 0 26px; }
.eyebrow { color:var(--acento); font-size:.78rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(205px,1fr)); gap:0;
         border-block:1px solid var(--borda); margin:23px 0 20px; }
.card { padding:16px 19px 17px; border-left:1px solid var(--borda); min-width:0; }
.card:first-child { border-left:0; padding-left:0; }
.card-label { color:var(--suave); font-size:.82rem; }
.card-value { font-size:1.8rem; line-height:1.25; font-weight:750; letter-spacing:-.03em;
              font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
.card-detail { color:var(--suave); font-size:.82rem; margin-top:3px; }
.note { margin:14px 0; padding:11px 15px; border-left:4px solid var(--acento);
        background:color-mix(in srgb,var(--acento) 7%,var(--fundo)); }
.note.warn { border-color:var(--alerta); background:color-mix(in srgb,var(--alerta) 8%,var(--fundo)); }
.note.error { border-color:var(--erro); background:color-mix(in srgb,var(--erro) 8%,var(--fundo)); }
.note.good { border-color:var(--sucesso); background:color-mix(in srgb,var(--sucesso) 7%,var(--fundo)); }
.muted { color:var(--suave); }
.flow { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:18px 0; }
.flow-item { border:1px solid var(--borda); border-radius:9px; padding:14px 16px; background:var(--papel); }
.flow-item strong { display:block; margin-bottom:4px; }
.eq { padding:11px 14px; margin:10px 0; border:1px solid var(--borda); border-radius:7px;
      background:var(--papel); font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
      overflow-x:auto; }
.two { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr)); gap:22px; align-items:start; }
.chart-card { border:1px solid var(--borda); border-radius:9px; padding:13px 14px 10px; min-width:0; }
.chart-card h3 { margin:0 0 4px; }
.chart-card p { color:var(--suave); font-size:.86rem; margin:6px 0 2px; }
.chart { overflow-x:auto; }
.chart svg { display:block; width:100%; height:auto; min-width:560px; }
svg { font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif; }
svg text { fill:var(--suave); font-size:11px; }
svg .axis { stroke:var(--texto); stroke-width:1.3; fill:none; }
svg .grid { stroke:var(--grade); stroke-width:1; }
svg .line-main { stroke:var(--acento); stroke-width:2.5; fill:none; stroke-linejoin:round; stroke-linecap:round; }
svg .point-main { fill:var(--acento); stroke:var(--fundo); stroke-width:1.1; }
svg .line-grid { stroke:var(--acento); stroke-width:2.5; fill:none; stroke-linejoin:round; stroke-linecap:round; }
svg .point-search { fill:var(--secundaria); stroke:var(--texto); stroke-width:.7; }
svg .point-best { fill:var(--terciaria); stroke:var(--fundo); stroke-width:1.4; }
svg .threshold { stroke:var(--erro); stroke-width:1.4; stroke-dasharray:6 4; }
svg .bar-l { fill:var(--acento); }
svg .bar-v { fill:var(--secundaria); }
svg .small-title { fill:var(--texto); font-size:12px; font-weight:700; }
.legend { display:flex; flex-wrap:wrap; gap:16px; margin:7px 2px 0; color:var(--suave); font-size:.82rem; }
.legend span { display:inline-flex; align-items:center; gap:6px; }
.swatch { display:inline-block; width:12px; height:9px; border-radius:2px; }
.table-scroll { overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:.86rem; font-variant-numeric:tabular-nums; }
th,td { padding:7px 10px; border-bottom:1px solid var(--borda); text-align:right; white-space:nowrap; }
th { border-bottom:2px solid var(--texto); font-weight:700; }
th:first-child,td:first-child { text-align:left; }
tr:hover td { background:var(--papel); }
details { margin:12px 0; border-top:1px solid var(--borda); padding-top:9px; }
summary { cursor:pointer; color:var(--acento); font-weight:650; }
code { padding:1px 5px; border-radius:4px; background:var(--papel); }
a { color:var(--acento); }
[hidden] { display:none !important; }
.controles { display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; margin:2px 0 10px; font-size:.86rem; }
.botao { font:inherit; font-size:.86rem; font-weight:650; padding:6px 14px; border:1px solid var(--acento);
         border-radius:7px; background:var(--fundo); color:var(--acento); cursor:pointer; }
.botao:hover { background:color-mix(in srgb,var(--acento) 10%,var(--fundo)); }
.botao[aria-pressed="true"] { background:var(--acento); color:var(--fundo); }
.botao:focus-visible { outline:2px solid var(--acento); outline-offset:2px; }
svg .serie .curva { stroke:hsl(var(--h) 72% var(--lum)); stroke-width:2; fill:none; stroke-linejoin:round; stroke-linecap:round; }
svg .serie .ponto-curva { fill:hsl(var(--h) 72% var(--lum)); stroke:var(--fundo); stroke-width:.8; }
svg .serie:hover .curva { stroke-width:3.6; }
svg .serie-exp .curva { stroke:var(--texto); stroke-width:2.4; stroke-dasharray:7 4; }
svg .serie-exp .ponto-curva { fill:var(--texto); }
svg .serie-exp:hover .curva { stroke-width:3.6; }
svg .ponto-calc { fill:none; stroke:var(--texto); stroke-width:1.6; }
.swatch-exp { background:var(--texto); }
.footer { margin-top:42px; padding-top:14px; border-top:1px solid var(--borda); color:var(--suave); font-size:.82rem; }
@media(max-width:650px) {
  main { padding:25px 15px 55px; }
  h1 { font-size:1.75rem; }
  .card { padding:12px 10px; }
  .card:first-child { padding-left:0; }
}
"""
