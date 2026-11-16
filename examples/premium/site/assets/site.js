/* Alto Lume v2 · comportamento do site. Cada parte só roda se a página tiver o bloco. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const EXEMPLO = true;

  /* ---------- aviso dos botões de exemplo (no site do cliente, abrem de verdade) ---------- */
  const toast = $('#toast');
  let tId;
  function avisar(html) {
    if (!toast) return;
    toast.innerHTML = html;
    toast.classList.add('is-on');
    clearTimeout(tId);
    tId = setTimeout(() => toast.classList.remove('is-on'), 7000);
  }
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function whatsapp(msg) {
    const title = root.lang.startsWith('en') ? 'Message preview' : root.lang.startsWith('es') ? 'Vista previa del mensaje' : 'Prévia da mensagem';
    avisar(`<b>${esc(title)}</b><q>${esc(msg)}</q>`);
  }
  // só links: o <html> também tem data-exemplo (modo do site) e não pode entrar aqui
  $$('a[data-exemplo]').forEach((a) => a.addEventListener('click', (e) => {
    if (a.dataset.exemplo === 'whatsapp') { e.preventDefault(); whatsapp(a.dataset.msg || 'Olá! Quero saber mais sobre o Alto Lume.'); }
    else if (EXEMPLO) { e.preventDefault(); avisar(`<b>${root.lang.startsWith('pt') ? 'Isto é um exemplo.' : 'Example.'}</b> ${esc(a.dataset.aviso || 'No site do cliente, este link abre o endereço dele no mapa.')}`); }
  }));

  /* ---------- tema claro ou escuro ---------- */
  $$('.tema').forEach((b) => b.addEventListener('click', () => {
    const atual = root.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    const novo = atual === 'light' ? 'dark' : 'light';
    root.dataset.theme = novo;
    b.setAttribute('aria-pressed', String(novo === 'light'));
    try { localStorage.setItem('alto-lume-tema', novo); } catch (e) {}
  }));

  /* ---------- barra do topo: transparente sobre a foto, escura depois da rolagem ---------- */
  const barra = $('.top--hero');
  if (barra) {
    const f = () => barra.classList.toggle('is-solido', scrollY > 40);
    addEventListener('scroll', f, { passive: true }); f();
  }

  /* ---------- menu do celular ---------- */
  const burger = $('.burger'), sheet = $('#menu');
  if (burger && sheet) {
    const menu = (open) => {
      root.classList.toggle('menu-open', open);
      burger.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) sheet.querySelector('a').focus();
    };
    burger.addEventListener('click', () => menu(true));
    $('.fechar', sheet).addEventListener('click', () => { menu(false); burger.focus(); });
    $$('a', sheet).forEach((a) => a.addEventListener('click', () => menu(false)));
    addEventListener('keydown', (e) => { if (e.key === 'Escape' && root.classList.contains('menu-open')) { menu(false); burger.focus(); } });
    addEventListener('resize', () => { if (innerWidth > 1100 && root.classList.contains('menu-open')) menu(false); });
  }

  /* ---------- topo: troca de hora (manhã, entardecer, noite) ---------- */
  const fotos = $$('.hero__media img');
  const abas = $$('.scenes__tabs [role="tab"]');
  if (fotos.length && abas.length) {
    let ativa = fotos.findIndex((f) => f.classList.contains('is-active')), auto = !reduce, timer;
    const mostrar = (i) => {
      if (i === ativa) return;
      fotos[ativa].classList.remove('is-active');
      void fotos[i].offsetWidth;            // reinicia a aproximação lenta
      fotos[i].classList.add('is-active');
      abas[ativa].setAttribute('aria-selected', 'false'); abas[ativa].tabIndex = -1;
      abas[i].setAttribute('aria-selected', 'true'); abas[i].tabIndex = 0;
      ativa = i;
    };
    abas.forEach((aba, i) => {
      aba.addEventListener('click', () => { auto = false; clearInterval(timer); mostrar(i); });
      aba.addEventListener('keydown', (e) => {
        const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
        if (!d) return;
        e.preventDefault(); auto = false; clearInterval(timer);
        const n = (ativa + d + abas.length) % abas.length; mostrar(n); abas[n].focus();
      });
    });
    if (auto) timer = setInterval(() => { if (!document.hidden) mostrar((ativa + 1) % fotos.length); }, 9000);
    // botão de pausa: para a troca automática e a aproximação lenta (critério 2.2.2 da WCAG)
    const hero = $('.hero'), pausar = $('.pausar');
    if (pausar) pausar.addEventListener('click', () => {
      const parado = !hero.classList.contains('parado');
      hero.classList.toggle('parado', parado);
      pausar.setAttribute('aria-pressed', String(parado));
      $('span', pausar).textContent = parado ? pausar.dataset.continuar : pausar.dataset.pausar;
      if (parado) { auto = false; clearInterval(timer); }
    });
  }
  const hora = $('#hora');
  if (hora) {
    const tick = () => { hora.textContent = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }).format(new Date()); };
    tick(); setInterval(tick, 30000);
  }

  /* ---------- manifesto: as palavras acendem com a rolagem ---------- */
  const man = $('#manifesto');
  if (man) {
    man.innerHTML = man.textContent.trim().split(/\s+/).map((w) => `<span class="w">${w}</span>`).join(' ');
    const words = $$('.w', man);
    let pend = false;
    const paint = () => {
      pend = false;
      const r = man.getBoundingClientRect();
      const p = reduce ? 1 : Math.min(1, Math.max(0, (innerHeight * .85 - r.top) / (r.height + innerHeight * .35)));
      const lit = Math.round(p * words.length);
      words.forEach((w, i) => w.classList.toggle('on', i < lit));
    };
    addEventListener('scroll', () => { if (!pend) { pend = true; requestAnimationFrame(paint); } }, { passive: true });
    paint();
  }

  /* ---------- entradas das seções ---------- */
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .12 });
  $$('.reveal').forEach((el) => io.observe(el));

  /* ---------- experiências: a foto acompanha o item ---------- */
  const itens = $$('.exp__item'), quadros = $$('.exp__frame img'), cap = $('#exp-cap');
  if (itens.length && quadros.length) {
    const show = (i) => {
      itens.forEach((it, k) => it.classList.toggle('is-on', k === i));
      quadros.forEach((f, k) => f.classList.toggle('is-on', k === i));
      if (cap) cap.textContent = $('h3', itens[i]).textContent;
    };
    itens.forEach((it, i) => it.addEventListener('mouseenter', () => show(i)));
    const io2 = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting && !matchMedia('(hover: none)').matches) show(itens.indexOf(e.target)); }), { rootMargin: '-45% 0px -45% 0px' });
    itens.forEach((it) => io2.observe(it));
  }

  /* ---------- índice do artigo: marca a seção que está na tela ---------- */
  const links = $$('.indice a');
  if (links.length) {
    const alvos = links.map((a) => document.getElementById(a.hash.slice(1))).filter(Boolean);
    const io3 = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) links.forEach((a) => a.classList.toggle('is-on', a.hash === '#' + e.target.id));
    }), { rootMargin: '-20% 0px -70% 0px' });
    alvos.forEach((h) => io3.observe(h));
  }

  /* ---------- galeria: foto ampliada ---------- */
  const caixa = $('#lightbox');
  if (caixa) {
    const img = $('img', caixa), leg = $('p', caixa);
    $$('[data-ampliar]').forEach((b) => b.addEventListener('click', () => {
      img.src = b.dataset.ampliar; img.alt = $('img', b).alt; leg.textContent = $('img', b).alt;
      caixa.showModal();
    }));
    $('.icone-btn', caixa).addEventListener('click', () => caixa.close());
    caixa.addEventListener('click', (e) => { if (e.target === caixa) caixa.close(); });
  }

  /* ---------- reserva: valor na hora e mensagem pronta ---------- */
  const f = $('#form-reserva');
  if (f) {
    const inp = $('#in', f), out = $('#out', f), hosp = $('#hosp', f);
    const err = $('#err', f), sumTxt = $('#sum-txt', f), sumVal = $('#sum-val', f);
    const L = JSON.parse(f.dataset.textos);
    const brl = (n) => n.toLocaleString(L.locale, { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
    const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10);
    const fmt = (s) => s.split('-').reverse().join('/');
    const hoje = new Date();
    const ini = new Date(hoje); ini.setDate(ini.getDate() + 14 + ((5 - ini.getDay() + 7) % 7));
    const fim = new Date(ini); fim.setDate(fim.getDate() + 2);
    inp.min = out.min = iso(hoje); inp.value = iso(ini); out.value = iso(fim);
    const pre = new URLSearchParams(location.search).get('suite');
    if (pre) { const r = $(`input[name="suite"][value="${CSS.escape(pre)}"]`, f); if (r) r.checked = true; }
    const estado = () => {
      const n = Math.round((new Date(out.value) - new Date(inp.value)) / 864e5), pessoas = +hosp.value;
      $$('input[name="suite"]', f).forEach((r) => { const off = pessoas > +r.dataset.max; r.disabled = off; r.closest('.opt').classList.toggle('is-off', off); });
      let s = $('input[name="suite"]:checked', f);
      if (!s || s.disabled) { s = $('input[name="suite"]:not(:disabled)', f); s.checked = true; }
      return { s, n, pessoas };
    };
    const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
    const FERIADOS = new Set((f.dataset.feriados || '').split(',').filter(Boolean));
    const dia = (s) => new Date(s + 'T12:00');
    // regra da casa: estadia com noite de sábado, de feriado ou de véspera de feriado pede no mínimo 2 noites
    const pedeDuas = (de, n) => {
      for (let i = 0; i < n; i++) {
        const d = dia(de); d.setDate(d.getDate() + i);
        const amanha = new Date(d); amanha.setDate(d.getDate() + 1);
        if (d.getDay() === 6 || FERIADOS.has(iso(d)) || FERIADOS.has(iso(amanha))) return true;
      }
      return false;
    };
    const calc = () => {
      const { s, n, pessoas } = estado();
      const falha = (msg) => { sumTxt.textContent = L.escolha; sumVal.textContent = '—'; err.textContent = msg; return null; };
      if (!inp.value || !out.value) return falha('');
      if (inp.value < iso(hoje)) return falha(L.erroPassado);
      if (!(n > 0)) return falha(L.erroDatas);
      if (n < 2 && pedeDuas(inp.value, n)) return falha(L.erroMinimo);
      // 10% a partir de 5 noites, se nenhuma noite cair em feriado ou véspera (regra escrita no site)
      let feriado = false;
      for (let i = 0; i < n; i++) { const d = dia(inp.value); d.setDate(d.getDate() + i); const a = new Date(d); a.setDate(d.getDate() + 1); if (FERIADOS.has(iso(d)) || FERIADOS.has(iso(a))) feriado = true; }
      const desconto = n >= 5 && !feriado;
      const total = Math.round(n * +s.dataset.preco * (desconto ? .9 : 1));
      sumTxt.innerHTML = `${plural(n, L.noite, L.noites)} · ${esc(s.dataset.nome)}<br>${plural(pessoas, L.pessoa, L.pessoas)} · ${L.cafe}${desconto ? '<br>' + L.desconto : ''}`;
      sumVal.textContent = brl(total);
      err.textContent = '';
      return { nome: s.dataset.nome, n, pessoas, total };
    };
    inp.addEventListener('change', () => {
      if (inp.value && (!out.value || out.value <= inp.value)) { const d = new Date(inp.value + 'T12:00'); d.setDate(d.getDate() + 2); out.value = iso(d); }
      out.min = inp.value || iso(hoje); calc();
    });
    [out, hosp].forEach((el) => el.addEventListener('change', calc));
    f.addEventListener('change', (e) => { if (e.target.name === 'suite') calc(); });
    f.addEventListener('submit', (e) => {
      e.preventDefault();
      const r = calc();
      if (!r) { if (!err.textContent) err.textContent = L.escolha; (inp.value < iso(hoje) ? inp : out).focus(); return; }
      whatsapp(L.msg.replace('{suite}', r.nome).replace('{de}', fmt(inp.value)).replace('{ate}', fmt(out.value))
        .replace('{noites}', plural(r.n, L.noite, L.noites)).replace('{pessoas}', plural(r.pessoas, L.pessoa, L.pessoas)).replace('{valor}', brl(r.total)));
    });
    calc();
  }

  /* ---------- contato: monta a mensagem do WhatsApp ---------- */
  const fc = $('#form-contato');
  if (fc) fc.addEventListener('submit', (e) => {
    e.preventDefault();
    const nome = $('#c-nome', fc).value.trim(), assunto = $('#c-assunto', fc).value, texto = $('#c-texto', fc).value.trim();
    const erro = $('#c-erro', fc);
    if (!nome || !texto) { erro.textContent = 'Escreva o seu nome e a mensagem.'; (nome ? $('#c-texto', fc) : $('#c-nome', fc)).focus(); return; }
    erro.textContent = '';
    whatsapp(`Olá! Sou ${nome}. Assunto: ${assunto}. ${texto}`);
  });
})();
